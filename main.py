from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
import uvicorn
import httpx
from datetime import datetime

app = FastAPI(title="API de Evaluación de Personalidad")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Supabase
SUPABASE_URL = "https://gbkhkbfbarsnpbdkxzii.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdia2hrYmZiYXJzbnBiZGt4emlpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQzODAzNzMsImV4cCI6MjA0OTk1NjM3M30.mcOcC2GVEu_wD3xNBzSCC3MwDck3CIdmz4D8adU-bpI"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Configuración de posiciones
POSITIONS = {
    "almacen": {
        "name": "Almacén",
        "tests": ["terman", "competencias", "disc"],
        "description": "Evaluación para posición de Almacén"
    },
    "ventas_mostrador": {
        "name": "Ventas a Mostrador",
        "tests": ["terman", "competencias", "disc"],
        "description": "Evaluación para posición de Ventas a Mostrador"
    },
    "pueblaventas": {
        "name": "Ventas a Mostrador",
        "tests": ["terman", "competencias", "disc"],
        "description": "Evaluación para posición de Ventas a Mostrador"
    }
}

# Preguntas DISC - En Español
DISC_QUESTIONS = [
    ("Me gusta tomar el mando cuando se necesitan tomar decisiones.", "D"),
    ("Disfruto persuadir a otros para que se entusiasmen con mis ideas.", "I"),
    ("Prefiero rutinas estables en lugar de cambios frecuentes.", "S"),
    ("Me enfoco fuertemente en la precisión y la calidad.", "C"),
    ("Me siento cómodo tomando decisiones rápidas con información limitada.", "D"),
    ("Disfruto trabajar con muchas personas diferentes.", "I"),
    ("Soy paciente cuando los procesos toman tiempo.", "S"),
    ("Reviso mi trabajo dos veces antes de entregarlo.", "C"),
    ("Presiono fuerte para lograr resultados.", "D"),
    ("Me siento energizado por la interacción social en el trabajo.", "I"),
    ("Valoro la lealtad y la consistencia en los equipos.", "S"),
    ("Sigo las reglas y procedimientos cuidadosamente.", "C"),
    ("Soy competitivo en alcanzar metas.", "D"),
    ("Motivo naturalmente a otros.", "I"),
    ("Prefiero la cooperación sobre la confrontación.", "S"),
    ("Me gusta analizar los detalles antes de actuar.", "C"),
    ("Me siento cómodo desafiando las ideas de otros.", "D"),
    ("Disfruto ser reconocido por mi trabajo.", "I"),
    ("Me mantengo calmado incluso cuando el trabajo se vuelve repetitivo.", "S"),
    ("Prefiero expectativas y pautas claras.", "C"),
    ("Me muevo rápidamente de la idea a la acción.", "D"),
    ("Disfruto de conversaciones informales en el trabajo.", "I"),
    ("Apoyo las decisiones del equipo incluso si inicialmente no estoy de acuerdo.", "S"),
    ("Valoro la precisión sobre la velocidad.", "C"),
    ("Tomo riesgos para lograr mejores resultados.", "D"),
    ("Soy optimista incluso bajo presión.", "I"),
    ("Evito los cambios repentinos cuando es posible.", "S"),
    ("Disfruto organizar información y sistemas.", "C"),
    ("Me gusta establecer objetivos ambiciosos.", "D"),
    ("Adapto mi estilo de comunicación a diferentes personas.", "I")
]

# Preguntas Big Five - En Español (Expandidas a 50 preguntas)
BIG5_QUESTIONS = [
    # Apertura a la Experiencia (10 preguntas)
    ("Busco activamente nuevas experiencias e ideas.", "O", False),
    ("Disfruto explorar soluciones creativas a los problemas.", "O", False),
    ("Me atrae aprender sobre temas diversos.", "O", False),
    ("Aprecio el arte, la belleza y los conceptos complejos.", "O", False),
    ("Cuestiono los enfoques tradicionales y pienso de manera innovadora.", "O", False),
    ("Me gusta experimentar con nuevas formas de hacer las cosas.", "O", False),
    ("Tengo una imaginación activa y creativa.", "O", False),
    ("Busco experiencias intelectualmente estimulantes.", "O", False),
    ("Me interesa comprender teorías y conceptos abstractos.", "O", False),
    ("Disfruto debatir ideas filosóficas y profundas.", "O", False),
    
    # Consciencia (10 preguntas)
    ("Completo proyectos a tiempo y con altos estándares.", "C", False),
    ("Organizo mi entorno de trabajo y horario de manera eficiente.", "C", False),
    ("Cumplo con mis compromisos de manera confiable.", "C", False),
    ("Planeo con anticipación y me preparo a fondo.", "C", False),
    ("Presto atención a detalles que otros podrían pasar por alto.", "C", False),
    ("Sigo un plan sistemático para alcanzar mis objetivos.", "C", False),
    ("Mantengo mis espacios de trabajo ordenados y organizados.", "C", False),
    ("Establezco metas claras y trabajo consistentemente hacia ellas.", "C", False),
    ("Verifico mi trabajo minuciosamente antes de considerarlo terminado.", "C", False),
    ("Soy disciplinado en mis hábitos de trabajo.", "C", False),
    
    # Extraversión (10 preguntas)
    ("Me siento energizado después de pasar tiempo con grupos.", "E", False),
    ("Disfruto ser el centro de atención.", "E", False),
    ("Inicio conversaciones con nuevas personas fácilmente.", "E", False),
    ("Expreso mis pensamientos y sentimientos abiertamente.", "E", False),
    ("Busco actividades sociales y reuniones.", "E", False),
    ("Me siento cómodo hablando frente a grupos grandes.", "E", False),
    ("Tomo la iniciativa en situaciones sociales.", "E", False),
    ("Disfruto trabajar en equipos grandes y dinámicos.", "E", False),
    ("Me describirían como una persona enérgica y entusiasta.", "E", False),
    ("Prefiero ambientes de trabajo animados y sociales.", "E", False),
    
    # Amabilidad (10 preguntas)
    ("Muestro preocupación genuina por el bienestar de otros.", "A", False),
    ("Busco puntos en común y construyo consenso.", "A", False),
    ("Ofrezco ayuda antes de que me la pidan.", "A", False),
    ("Trato a todos con respeto y amabilidad.", "A", False),
    ("Confío en las intenciones de las personas y les doy el beneficio de la duda.", "A", False),
    ("Soy comprensivo cuando otros cometen errores.", "A", False),
    ("Pongo las necesidades del equipo por encima de las mías propias.", "A", False),
    ("Evito conflictos innecesarios y busco armonía.", "A", False),
    ("Escucho activamente las preocupaciones de los demás.", "A", False),
    ("Soy generoso con mi tiempo y recursos para ayudar a otros.", "A", False),
    
    # Estabilidad Emocional (10 preguntas)
    ("Me mantengo calmado bajo presión.", "N", False),
    ("Me recupero rápidamente de las decepciones.", "N", False),
    ("Mantengo la perspectiva durante períodos estresantes.", "N", False),
    ("Enfrento los desafíos con confianza.", "N", False),
    ("Regulo mis emociones efectivamente.", "N", False),
    ("Mantengo un estado de ánimo estable en el trabajo.", "N", False),
    ("No me dejo abrumar fácilmente por situaciones difíciles.", "N", False),
    ("Puedo manejar críticas constructivas sin sentirme mal.", "N", False),
    ("Me adapto bien a cambios inesperados.", "N", False),
    ("Mantengo la compostura en situaciones de alta presión.", "N", False),
    
    # Preguntas inversas
    ("A menudo me preocupo por cosas que podrían salir mal.", "N", True),
    ("Dejo tareas sin terminar cuando pierdo interés.", "C", True),
    ("Evito probar nuevos enfoques.", "O", True),
    ("Me irrito fácilmente con las personas.", "A", True),
    ("Tengo dificultades para mantener mi espacio de trabajo organizado.", "C", True),
    ("Prefiero trabajar solo en lugar de en grupo.", "E", True),
    ("Me cuesta confiar en los demás.", "A", True),
    ("Evito situaciones donde tenga que hablar en público.", "E", True),
    ("Me estreso fácilmente por plazos ajustados.", "N", True),
    ("Rara vez cuestiono la forma establecida de hacer las cosas.", "O", True),
]

# Preguntas MBTI - En Español (60 preguntas)
MBTI_QUESTIONS = [
    # Extraversión (E) vs Introversión (I) - 15 preguntas
    ("Gano energía interactuando con colegas durante el día de trabajo.", "E", False),
    ("Prefiero trabajar en un espacio tranquilo con pocas interrupciones.", "I", False),
    ("Me siento cómodo presentando ideas en reuniones grandes.", "E", False),
    ("Necesito tiempo a solas para procesar información compleja.", "I", False),
    ("Disfruto hacer networking en eventos profesionales.", "E", False),
    ("Pienso mejor cuando trabajo de manera independiente.", "I", False),
    ("Me gusta discutir problemas en voz alta con mi equipo.", "E", False),
    ("Prefiero comunicarme por escrito que en persona.", "I", False),
    ("Me siento energizado después de un día lleno de reuniones.", "E", False),
    ("Valoro tener control sobre cuándo interactúo con otros.", "I", False),
    ("Inicio conversaciones fácilmente con personas en la oficina.", "E", False),
    ("Prefiero observar antes de participar en discusiones grupales.", "I", False),
    ("Me describirían como expresivo y entusiasta en el trabajo.", "E", False),
    ("Necesito tiempo para reflexionar antes de compartir mis ideas.", "I", False),
    ("Disfruto proyectos que requieren mucha colaboración en equipo.", "E", False),
    
    # Sensación (S) vs Intuición (N) - 15 preguntas
    ("Me enfoco en los hechos y datos concretos al tomar decisiones.", "S", False),
    ("Me interesan las posibilidades futuras más que los detalles actuales.", "N", False),
    ("Prefiero instrucciones paso a paso y específicas.", "S", False),
    ("Veo patrones y conexiones que otros no notan.", "N", False),
    ("Confío en la experiencia práctica y métodos comprobados.", "S", False),
    ("Me gusta explorar teorías y conceptos abstractos.", "N", False),
    ("Presto atención a los detalles específicos de cada tarea.", "S", False),
    ("Pienso en cómo las cosas podrían ser diferentes o mejores.", "N", False),
    ("Valoro la precisión y exactitud en mi trabajo.", "S", False),
    ("Me atraen las ideas innovadoras y no convencionales.", "N", False),
    ("Prefiero trabajar con información tangible y real.", "S", False),
    ("Disfruto conceptualizar nuevos enfoques y estrategias.", "N", False),
    ("Me concentro en lo que está sucediendo en el presente.", "S", False),
    ("Pienso en las implicaciones a largo plazo de las decisiones.", "N", False),
    ("Sigo procedimientos establecidos que han funcionado antes.", "S", False),
    
    # Pensamiento (T) vs Sentimiento (F) - 15 preguntas
    ("Tomo decisiones basándome en análisis lógico y objetivo.", "T", False),
    ("Considero cómo mis decisiones afectarán a las personas.", "F", False),
    ("Valoro la eficiencia por encima de la armonía del equipo.", "T", False),
    ("Es importante para mí que todos se sientan escuchados.", "F", False),
    ("Puedo dar retroalimentación crítica sin sentirme incómodo.", "T", False),
    ("Me preocupa herir los sentimientos de otros con mis comentarios.", "F", False),
    ("Priorizo la objetividad al resolver conflictos.", "T", False),
    ("Busco soluciones que satisfagan las necesidades de todos.", "F", False),
    ("Las reglas deben aplicarse consistentemente sin excepciones.", "T", False),
    ("Las circunstancias personales deben considerarse al aplicar políticas.", "F", False),
    ("Me describirían como directo y franco.", "T", False),
    ("Me describirían como empático y considerado.", "F", False),
    ("Valoro la competencia técnica sobre las habilidades interpersonales.", "T", False),
    ("Creo que mantener buenas relaciones es esencial para el éxito.", "F", False),
    ("Analizo pros y contras antes de tomar decisiones importantes.", "T", False),
    
    # Juicio (J) vs Percepción (P) - 15 preguntas
    ("Prefiero tener un plan claro antes de comenzar un proyecto.", "J", False),
    ("Me gusta mantener mis opciones abiertas el mayor tiempo posible.", "P", False),
    ("Me siento incómodo con plazos indefinidos.", "J", False),
    ("Trabajo mejor bajo la presión de una fecha límite cercana.", "P", False),
    ("Hago listas detalladas y las sigo consistentemente.", "J", False),
    ("Soy flexible y me adapto fácilmente a cambios de última hora.", "P", False),
    ("Prefiero terminar tareas antes de comenzar nuevas.", "J", False),
    ("Disfruto trabajar en múltiples proyectos simultáneamente.", "P", False),
    ("Me gusta tener estructura y rutina en mi día de trabajo.", "J", False),
    ("Prefiero ambientes de trabajo espontáneos y variados.", "P", False),
    ("Tomo decisiones rápidamente para seguir adelante.", "J", False),
    ("Prefiero recopilar más información antes de decidir.", "P", False),
    ("Me siento satisfecho cuando completo tareas según lo planeado.", "J", False),
    ("Me gusta explorar diferentes enfoques mientras trabajo.", "P", False),
    ("Organizo mi espacio de trabajo de manera sistemática.", "J", False),
]

# Preguntas ALLPORT (Valores) - 40 preguntas
ALLPORT_QUESTIONS = [
    # Teórico (10 preguntas)
    ("Me motiva descubrir la verdad detrás de las cosas.", "T", False),
    ("Disfruto analizar problemas desde una perspectiva lógica.", "T", False),
    ("Prefiero tomar decisiones basadas en datos y hechos verificables.", "T", False),
    ("Me interesa comprender los principios fundamentales de cómo funcionan las cosas.", "T", False),
    ("Valoro el conocimiento por encima de las ganancias materiales.", "T", False),
    ("Dedico tiempo a investigar antes de formar una opinión.", "T", False),
    ("Me atraen las discusiones filosóficas e intelectuales.", "T", False),
    ("Prefiero la objetividad sobre las emociones al resolver problemas.", "T", False),
    ("Busco constantemente aprender cosas nuevas.", "T", False),
    ("Cuestiono las ideas establecidas para validar su veracidad.", "T", False),
    
    # Económico (10 preguntas)
    ("Me enfoco en la rentabilidad y eficiencia en mi trabajo.", "E", False),
    ("Valoro las recompensas tangibles por mi esfuerzo.", "E", False),
    ("Prefiero invertir mi tiempo en actividades que generen retorno económico.", "E", False),
    ("Considero el costo-beneficio antes de tomar decisiones importantes.", "E", False),
    ("Me motiva alcanzar la estabilidad financiera.", "E", False),
    ("Busco oportunidades para maximizar recursos.", "E", False),
    ("Prefiero soluciones prácticas que generen resultados medibles.", "E", False),
    ("Valoro la utilidad de las cosas más que su belleza.", "E", False),
    ("Me interesa el crecimiento económico y la prosperidad.", "E", False),
    ("Tomo decisiones pensando en el valor que aportan.", "E", False),
    
    # Estético (5 preguntas)
    ("Aprecio la belleza y la armonía en mi entorno.", "A", False),
    ("Me inspiran las expresiones artísticas y creativas.", "A", False),
    ("Valoro el diseño y la presentación de las cosas.", "A", False),
    ("Busco experiencias que estimulen mis sentidos.", "A", False),
    ("Me importa que mi espacio de trabajo sea estéticamente agradable.", "A", False),
    
    # Social (5 preguntas)
    ("Me motiva ayudar a otros a alcanzar su potencial.", "S", False),
    ("Valoro las relaciones humanas por encima del éxito material.", "S", False),
    ("Me satisface contribuir al bienestar de los demás.", "S", False),
    ("Prefiero trabajar en proyectos que beneficien a la sociedad.", "S", False),
    ("Dedico tiempo a causas altruistas y de servicio.", "S", False),
    
    # Político (5 preguntas)
    ("Me motiva tener influencia y liderazgo.", "P", False),
    ("Busco posiciones de autoridad y reconocimiento.", "P", False),
    ("Valoro el poder para generar cambios importantes.", "P", False),
    ("Me interesa competir y destacar sobre otros.", "P", False),
    ("Disfruto dirigir equipos y proyectos estratégicos.", "P", False),
    
    # Religioso (5 preguntas)
    ("Busco un propósito trascendental en mi vida.", "R", False),
    ("Valoro la conexión con algo más grande que yo mismo.", "R", False),
    ("Me guían principios éticos y valores profundos.", "R", False),
    ("Busco coherencia entre mis acciones y mis creencias.", "R", False),
    ("Me importa el significado espiritual de mi trabajo.", "R", False),
]

# Preguntas TERMAN (Razonamiento) - 35 preguntas
TERMAN_QUESTIONS = [
    # Razonamiento Verbal (10 preguntas)
    ("Puedo identificar rápidamente sinónimos y antónimos de palabras complejas.", "V", False),
    ("Comprendo fácilmente textos técnicos y especializados.", "V", False),
    ("Puedo explicar conceptos abstractos con claridad.", "V", False),
    ("Identifico rápidamente la idea principal en documentos extensos.", "V", False),
    ("Tengo facilidad para expresar ideas complejas de forma simple.", "V", False),
    ("Analizo el significado profundo de los mensajes más allá de lo literal.", "V", False),
    ("Comprendo analogías y metáforas con facilidad.", "V", False),
    ("Puedo argumentar diferentes perspectivas de un mismo tema.", "V", False),
    ("Identifico inconsistencias lógicas en argumentos verbales.", "V", False),
    ("Aprendo vocabulario nuevo rápidamente.", "V", False),
    
    # Razonamiento Lógico-Matemático (10 preguntas)
    ("Resuelvo problemas numéricos mentalmente con facilidad.", "M", False),
    ("Identifico patrones en secuencias numéricas rápidamente.", "M", False),
    ("Comprendo y aplico fórmulas matemáticas sin dificultad.", "M", False),
    ("Puedo estimar resultados numéricos con precisión.", "M", False),
    ("Analizo datos estadísticos de forma natural.", "M", False),
    ("Resuelvo problemas de lógica de manera sistemática.", "M", False),
    ("Me resulta fácil trabajar con porcentajes y proporciones.", "M", False),
    ("Identifico relaciones causa-efecto en sistemas complejos.", "M", False),
    ("Puedo construir argumentos lógicos paso a paso.", "M", False),
    ("Detecto errores en cálculos o razonamientos numéricos.", "M", False),
    
    # Razonamiento Espacial (8 preguntas)
    ("Visualizo objetos tridimensionales en mi mente fácilmente.", "S", False),
    ("Me oriento bien en espacios nuevos.", "S", False),
    ("Puedo imaginar cómo se vería un objeto desde diferentes ángulos.", "S", False),
    ("Comprendo planos, mapas y diagramas sin dificultad.", "S", False),
    ("Visualizo el resultado final antes de armar o construir algo.", "S", False),
    ("Identifico relaciones espaciales entre objetos rápidamente.", "S", False),
    ("Puedo rotar mentalmente figuras complejas.", "S", False),
    ("Tengo facilidad para leer e interpretar gráficos.", "S", False),
    
    # Comprensión y Análisis (7 preguntas)
    ("Identifico rápidamente qué información es relevante y cuál no.", "C", False),
    ("Puedo sintetizar información de múltiples fuentes.", "C", False),
    ("Analizo problemas desde múltiples perspectivas antes de decidir.", "C", False),
    ("Identifico suposiciones ocultas en argumentos.", "C", False),
    ("Puedo anticipar consecuencias de diferentes cursos de acción.", "C", False),
    ("Integro información nueva con conocimiento previo fácilmente.", "C", False),
    ("Evalúo la credibilidad de las fuentes de información.", "C", False),
]

# Preguntas COMPETENCIAS (70 preguntas - 10 competencias clave)
COMPETENCIAS_QUESTIONS = [
    # 1. Liderazgo (10 preguntas)
    ("Tomo la iniciativa para dirigir proyectos y equipos.", "LID", False),
    ("Inspiro a otros a dar lo mejor de sí mismos.", "LID", False),
    ("Tomo decisiones difíciles cuando es necesario.", "LID", False),
    ("Delego tareas de manera efectiva.", "LID", False),
    ("Mantengo la visión del equipo enfocada en los objetivos.", "LID", False),
    ("Genero confianza en mi equipo.", "LID", False),
    ("Motivo a otros incluso en situaciones adversas.", "LID", False),
    ("Doy retroalimentación constructiva regularmente.", "LID", False),
    ("Desarrollo el potencial de las personas a mi cargo.", "LID", False),
    ("Asumo responsabilidad por los resultados del equipo.", "LID", False),
    
    # 2. Comunicación (10 preguntas)
    ("Me expreso con claridad tanto verbalmente como por escrito.", "COM", False),
    ("Adapto mi comunicación según la audiencia.", "COM", False),
    ("Escucho activamente antes de responder.", "COM", False),
    ("Hago presentaciones efectivas y persuasivas.", "COM", False),
    ("Comunico ideas complejas de forma comprensible.", "COM", False),
    ("Manejo conversaciones difíciles con diplomacia.", "COM", False),
    ("Hago preguntas que generan claridad.", "COM", False),
    ("Sintetizo información de manera concisa.", "COM", False),
    ("Leo e interpreto correctamente el lenguaje no verbal.", "COM", False),
    ("Doy seguimiento efectivo a compromisos comunicados.", "COM", False),
    
    # 3. Trabajo en Equipo (8 preguntas)
    ("Colaboro efectivamente con personas de diferentes áreas.", "TEQ", False),
    ("Contribuyo al logro de objetivos comunes.", "TEQ", False),
    ("Apoyo a mis compañeros cuando lo necesitan.", "TEQ", False),
    ("Resuelvo conflictos constructivamente.", "TEQ", False),
    ("Comparto información y conocimiento libremente.", "TEQ", False),
    ("Acepto y valoro opiniones diferentes a las mías.", "TEQ", False),
    ("Mantengo una actitud positiva en el equipo.", "TEQ", False),
    ("Construyo relaciones de confianza con colegas.", "TEQ", False),
    
    # 4. Adaptabilidad (8 preguntas)
    ("Me ajusto rápidamente a cambios en prioridades.", "ADA", False),
    ("Mantengo efectividad en ambientes de incertidumbre.", "ADA", False),
    ("Aprendo nuevas habilidades con facilidad.", "ADA", False),
    ("Veo los cambios como oportunidades.", "ADA", False),
    ("Modifico mi enfoque cuando las circunstancias lo requieren.", "ADA", False),
    ("Trabajo efectivamente con diferentes estilos de trabajo.", "ADA", False),
    ("Manejo múltiples proyectos simultáneamente.", "ADA", False),
    ("Me recupero rápidamente de contratiempos.", "ADA", False),
    
    # 5. Pensamiento Crítico (8 preguntas)
    ("Analizo situaciones desde múltiples perspectivas.", "PEN", False),
    ("Identifico la raíz de los problemas efectivamente.", "PEN", False),
    ("Evalúo pros y contras antes de tomar decisiones.", "PEN", False),
    ("Cuestiono suposiciones para validar ideas.", "PEN", False),
    ("Distingo entre hechos y opiniones.", "PEN", False),
    ("Aplico lógica para resolver problemas complejos.", "PEN", False),
    ("Anticipo consecuencias de diferentes alternativas.", "PEN", False),
    ("Sintetizo información de fuentes diversas.", "PEN", False),
    
    # 6. Orientación a Resultados (8 preguntas)
    ("Establezco metas ambiciosas y las alcanzo.", "RES", False),
    ("Mantengo el enfoque hasta completar tareas.", "RES", False),
    ("Supero obstáculos para lograr objetivos.", "RES", False),
    ("Mido mi progreso constantemente.", "RES", False),
    ("Priorizo actividades de alto impacto.", "RES", False),
    ("Cumplo plazos consistentemente.", "RES", False),
    ("Busco formas de mejorar la eficiencia.", "RES", False),
    ("Asumo responsabilidad por mis resultados.", "RES", False),
    
    # 7. Inteligencia Emocional (8 preguntas)
    ("Reconozco y gestiono mis emociones efectivamente.", "IE", False),
    ("Comprendo cómo se sienten los demás.", "IE", False),
    ("Manejo el estrés de manera saludable.", "IE", False),
    ("Mantengo la calma en situaciones de presión.", "IE", False),
    ("Entiendo cómo mis acciones afectan a otros.", "IE", False),
    ("Adapto mi respuesta emocional según el contexto.", "IE", False),
    ("Construyo rapport fácilmente con otros.", "IE", False),
    ("Uso las emociones de forma productiva.", "IE", False),
    
    # 8. Creatividad e Innovación (6 preguntas)
    ("Genero ideas originales para resolver problemas.", "CRE", False),
    ("Propongo mejoras a procesos existentes.", "CRE", False),
    ("Encuentro soluciones no convencionales.", "CRE", False),
    ("Combino ideas de diferentes áreas creativamente.", "CRE", False),
    ("Experimento con nuevos enfoques.", "CRE", False),
    ("Visualizo posibilidades que otros no ven.", "CRE", False),
    
    # 9. Planificación y Organización (6 preguntas)
    ("Planifico mi trabajo de manera sistemática.", "PLN", False),
    ("Establezco prioridades claras.", "PLN", False),
    ("Organizo recursos eficientemente.", "PLN", False),
    ("Anticipo necesidades futuras.", "PLN", False),
    ("Gestiono mi tiempo efectivamente.", "PLN", False),
    ("Mantengo sistemas organizados de trabajo.", "PLN", False),
    
    # 10. Negociación (6 preguntas)
    ("Logro acuerdos beneficiosos para todas las partes.", "NEG", False),
    ("Persuado a otros con argumentos sólidos.", "NEG", False),
    ("Identifico intereses comunes en negociaciones.", "NEG", False),
    ("Manejo objeciones constructivamente.", "NEG", False),
    ("Cierro acuerdos de manera efectiva.", "NEG", False),
    ("Mantengo relaciones positivas durante negociaciones.", "NEG", False),
]

class TestAnswers(BaseModel):
    name: str
    email: EmailStr
    phone: str
    position: str  # NUEVO: campo de posición
    test_type: str
    answers: List[int]

async def save_to_supabase(table: str, data: dict):
    """Guarda datos en Supabase"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=HEADERS,
            json=data
        )
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=500, detail=f"Error guardando en Supabase: {response.text}")
        return response.json()

def calculate_disc(answers: List[int]) -> Dict:
    scores = {"D": 0, "I": 0, "S": 0, "C": 0}
    for i, score in enumerate(answers):
        trait = DISC_QUESTIONS[i][1]
        scores[trait] += score
    
    total = sum(scores.values())
    percentages = {k: round((v/total)*100, 1) for k, v in scores.items()}
    dominant = max(scores, key=scores.get)
    
    descriptions = {
        "D": "Dominancia - Eres orientado a resultados, decisivo y te gustan los desafíos. Tomas el mando y te enfocas en lograr objetivos.",
        "I": "Influencia - Eres entusiasta, optimista y orientado a las personas. Sobresales motivando e inspirando a otros.",
        "S": "Estabilidad - Eres paciente, colaborador y confiable. Creas ambientes estables y valoras el trabajo en equipo.",
        "C": "Conciencia - Eres analítico, preciso y enfocado en la calidad. Valoras la exactitud y los enfoques sistemáticos."
    }
    
    return {
        "scores": scores,
        "percentages": percentages,
        "dominant": dominant,
        "description": descriptions[dominant]
    }

def calculate_big5(answers: List[int]) -> Dict:
    scores = {"O": 0, "C": 0, "E": 0, "A": 0, "N": 0}
    
    for i, score in enumerate(answers):
        trait = BIG5_QUESTIONS[i][1]
        is_reverse = BIG5_QUESTIONS[i][2]
        
        if is_reverse:
            adjusted_score = 6 - score
        else:
            adjusted_score = score
            
        scores[trait] += adjusted_score
    
    max_scores = {"O": 50, "C": 50, "E": 50, "A": 50, "N": 50}
    percentages = {k: round((v/max_scores[k])*100, 1) for k, v in scores.items()}
    
    trait_names = {
        "O": "Apertura a la Experiencia",
        "C": "Responsabilidad",
        "E": "Extraversión",
        "A": "Amabilidad",
        "N": "Estabilidad Emocional"
    }
    
    descriptions = {
        "O": "innovador, curioso y creativo" if percentages["O"] > 60 else "práctico y tradicional",
        "C": "organizado, disciplinado y confiable" if percentages["C"] > 60 else "flexible y espontáneo",
        "E": "extrovertido, energético y sociable" if percentages["E"] > 60 else "reservado e independiente",
        "A": "compasivo, cooperativo y confiado" if percentages["A"] > 60 else "analítico y directo",
        "N": "calmado, resiliente y confiado" if percentages["N"] > 60 else "sensible y reactivo"
    }
    
    return {
        "scores": scores,
        "percentages": percentages,
        "trait_names": trait_names,
        "descriptions": descriptions
    }

def calculate_mbti(answers: List[int]) -> Dict:
    # Inicializar puntajes para cada dimensión
    dimensions = {
        "E": 0, "I": 0,  # Extraversión vs Introversión
        "S": 0, "N": 0,  # Sensación vs Intuición
        "T": 0, "F": 0,  # Pensamiento vs Sentimiento
        "J": 0, "P": 0   # Juicio vs Percepción
    }
    
    for i, score in enumerate(answers):
        trait = MBTI_QUESTIONS[i][1]
        is_reverse = MBTI_QUESTIONS[i][2]
        
        if is_reverse:
            adjusted_score = 6 - score
        else:
            adjusted_score = score
        
        dimensions[trait] += adjusted_score
    
    # Determinar el tipo MBTI
    mbti_type = ""
    mbti_type += "E" if dimensions["E"] >= dimensions["I"] else "I"
    mbti_type += "S" if dimensions["S"] >= dimensions["N"] else "N"
    mbti_type += "T" if dimensions["T"] >= dimensions["F"] else "F"
    mbti_type += "J" if dimensions["J"] >= dimensions["P"] else "P"
    
    # Calcular porcentajes de preferencia
    percentages = {
        "E_I": round((dimensions["E"] / (dimensions["E"] + dimensions["I"])) * 100, 1),
        "S_N": round((dimensions["S"] / (dimensions["S"] + dimensions["N"])) * 100, 1),
        "T_F": round((dimensions["T"] / (dimensions["T"] + dimensions["F"])) * 100, 1),
        "J_P": round((dimensions["J"] / (dimensions["J"] + dimensions["P"])) * 100, 1)
    }
    
    # Descripciones detalladas orientadas al trabajo
    type_descriptions = {
        "ISTJ": "Inspector - Responsable, organizado y confiable. Excelente en roles que requieren precisión, seguimiento de procedimientos y gestión de detalles.",
        "ISFJ": "Protector - Servicial, leal y práctico. Sobresale en roles de soporte, servicio al cliente y mantenimiento de operaciones.",
        "INFJ": "Consejero - Visionario, empático y comprometido. Ideal para desarrollo organizacional, consultoría y roles de mentoría.",
        "INTJ": "Arquitecto - Estratégico, innovador y determinado. Excelente en planificación estratégica, análisis de sistemas y desarrollo de soluciones complejas.",
        "ISTP": "Artesano - Práctico, adaptable y analítico. Sobresale en resolución de problemas técnicos y situaciones que requieren pensamiento rápido.",
        "ISFP": "Compositor - Flexible, observador y sensible. Ideal para roles creativos, trabajo artístico y ambientes que valoran la individualidad.",
        "INFP": "Sanador - Idealista, creativo y empático. Excelente en escritura, consejería y roles que requieren autenticidad.",
        "INTP": "Pensador - Lógico, innovador y curioso. Sobresale en investigación, desarrollo de teorías y resolución de problemas complejos.",
        "ESTP": "Promotor - Enérgico, pragmático y directo. Ideal para ventas, negociación y situaciones que requieren acción rápida.",
        "ESFP": "Ejecutante - Entusiasta, espontáneo y amigable. Excelente en presentaciones, entretenimiento y roles centrados en personas.",
        "ENFP": "Campeón - Entusiasta, creativo y versátil. Sobresale en innovación, relaciones públicas y roles que requieren inspirar a otros.",
        "ENTP": "Visionario - Innovador, estratégico y carismático. Ideal para emprendimiento, consultoría estratégica y desarrollo de negocios.",
        "ESTJ": "Supervisor - Organizado, práctico y decidido. Excelente en gestión, administración y roles de liderazgo operacional.",
        "ESFJ": "Proveedor - Sociable, organizado y cooperativo. Sobresale en recursos humanos, coordinación de eventos y gestión de equipos.",
        "ENFJ": "Maestro - Carismático, inspirador y organizado. Ideal para liderazgo, capacitación y desarrollo de talento.",
        "ENTJ": "Comandante - Visionario, decisivo y estratégico. Excelente en liderazgo ejecutivo, planificación empresarial y transformación organizacional."
    }
    
    # Indicadores de desempeño laboral por tipo
    job_performance_indicators = {
        "ISTJ": "Alto desempeño en: Cumplimiento de plazos, exactitud, seguimiento de procedimientos. Desarrollo: Flexibilidad ante cambios.",
        "ISFJ": "Alto desempeño en: Servicio, lealtad, estabilidad operacional. Desarrollo: Asertividad y delegación.",
        "INFJ": "Alto desempeño en: Visión estratégica, empatía, desarrollo de personas. Desarrollo: Toma de decisiones difíciles.",
        "INTJ": "Alto desempeño en: Pensamiento estratégico, innovación, análisis. Desarrollo: Comunicación interpersonal.",
        "ISTP": "Alto desempeño en: Resolución práctica de problemas, eficiencia. Desarrollo: Planificación a largo plazo.",
        "ISFP": "Alto desempeño en: Creatividad, adaptabilidad, trabajo detallado. Desarrollo: Estructura y organización.",
        "INFP": "Alto desempeño en: Creatividad, autenticidad, valores. Desarrollo: Confrontación y pragmatismo.",
        "INTP": "Alto desempeño en: Análisis lógico, innovación conceptual. Desarrollo: Implementación y seguimiento.",
        "ESTP": "Alto desempeño en: Acción rápida, negociación, crisis. Desarrollo: Planificación y paciencia.",
        "ESFP": "Alto desempeño en: Energía, trabajo en equipo, presentación. Desarrollo: Enfoque en detalles.",
        "ENFP": "Alto desempeño en: Innovación, inspiración, conexiones. Desarrollo: Estructura y seguimiento.",
        "ENTP": "Alto desempeño en: Innovación, debate, emprendimiento. Desarrollo: Ejecución consistente.",
        "ESTJ": "Alto desempeño en: Organización, liderazgo, eficiencia. Desarrollo: Flexibilidad emocional.",
        "ESFJ": "Alto desempeño en: Colaboración, organización social. Desarrollo: Toma de decisiones difíciles.",
        "ENFJ": "Alto desempeño en: Liderazgo inspirador, desarrollo de talento. Desarrollo: Límites personales.",
        "ENTJ": "Alto desempeño en: Liderazgo estratégico, ejecución, resultados. Desarrollo: Empatía y paciencia."
    }
    
    return {
        "type": mbti_type,
        "dimensions": dimensions,
        "percentages": percentages,
        "description": type_descriptions.get(mbti_type, ""),
        "job_performance": job_performance_indicators.get(mbti_type, ""),
        "preferences": {
            "energy": "Extraversión" if mbti_type[0] == "E" else "Introversión",
            "information": "Sensación" if mbti_type[1] == "S" else "Intuición",
            "decisions": "Pensamiento" if mbti_type[2] == "T" else "Sentimiento",
            "lifestyle": "Juicio" if mbti_type[3] == "J" else "Percepción"
        }
    }

def calculate_allport(answers: List[int]) -> Dict:
    scores = {"T": 0, "E": 0, "A": 0, "S": 0, "P": 0, "R": 0}
    
    for i, score in enumerate(answers):
        value = ALLPORT_QUESTIONS[i][1]
        scores[value] += score
    
    max_scores = {"T": 50, "E": 50, "A": 25, "S": 25, "P": 25, "R": 25}
    percentages = {k: round((v/max_scores[k])*100, 1) for k, v in scores.items()}
    dominant = max(scores, key=scores.get)
    
    value_names = {
        "T": "Teórico", "E": "Económico", "A": "Estético",
        "S": "Social", "P": "Político", "R": "Religioso"
    }
    
    descriptions = {
        "T": "Valoras la verdad, el conocimiento y el pensamiento lógico.",
        "E": "Priorizas la utilidad, la eficiencia y los resultados prácticos.",
        "A": "Aprecias la belleza, la armonía y las expresiones creativas.",
        "S": "Te motiva ayudar a otros y contribuir al bienestar común.",
        "P": "Buscas influencia, liderazgo y poder.",
        "R": "Buscas significado trascendental y coherencia con principios profundos."
    }
    
    return {
        "scores": scores, "percentages": percentages, "dominant": dominant,
        "value_names": value_names, "description": descriptions[dominant],
        "all_descriptions": descriptions
    }

def calculate_terman(answers: List[int]) -> Dict:
    scores = {"V": 0, "M": 0, "S": 0, "C": 0}
    
    for i, score in enumerate(answers):
        ability = TERMAN_QUESTIONS[i][1]
        scores[ability] += score
    
    max_scores = {"V": 50, "M": 50, "S": 40, "C": 35}
    percentages = {k: round((v/max_scores[k])*100, 1) for k, v in scores.items()}
    total_percentage = sum(percentages.values()) / 4
    ci_estimate = round(85 + (total_percentage * 0.30))
    
    ability_names = {
        "V": "Razonamiento Verbal", "M": "Razonamiento Lógico-Matemático",
        "S": "Razonamiento Espacial", "C": "Comprensión y Análisis"
    }
    
    level = "Superior" if ci_estimate >= 110 else "Promedio Alto" if ci_estimate >= 100 else "Promedio"
    
    return {
        "scores": scores, "percentages": percentages, "ci_estimate": ci_estimate,
        "level": level, "ability_names": ability_names,
        "interpretation": f"Nivel {level} de razonamiento (CI estimado: {ci_estimate})."
    }

def calculate_competencias(answers: List[int]) -> Dict:
    scores = {
        "LID": 0, "COM": 0, "TEQ": 0, "ADA": 0, "PEN": 0,
        "RES": 0, "IE": 0, "CRE": 0, "PLN": 0, "NEG": 0
    }
    
    for i, score in enumerate(answers):
        competency = COMPETENCIAS_QUESTIONS[i][1]
        scores[competency] += score
    
    max_scores = {
        "LID": 50, "COM": 50, "TEQ": 40, "ADA": 40, "PEN": 40,
        "RES": 40, "IE": 40, "CRE": 30, "PLN": 30, "NEG": 30
    }
    
    percentages = {k: round((v/max_scores[k])*100, 1) for k, v in scores.items()}
    
    competency_names = {
        "LID": "Liderazgo", "COM": "Comunicación", "TEQ": "Trabajo en Equipo",
        "ADA": "Adaptabilidad", "PEN": "Pensamiento Crítico",
        "RES": "Orientación a Resultados", "IE": "Inteligencia Emocional",
        "CRE": "Creatividad e Innovación", "PLN": "Planificación y Organización",
        "NEG": "Negociación"
    }
    
    top_3 = sorted(percentages.items(), key=lambda x: x[1], reverse=True)[:3]
    areas_mejora = sorted(percentages.items(), key=lambda x: x[1])[:3]
    
    return {
        "scores": scores, "percentages": percentages,
        "competency_names": competency_names,
        "top_3": [(competency_names[k], v) for k, v in top_3],
        "areas_mejora": [(competency_names[k], v) for k, v in areas_mejora],
        "promedio_general": round(sum(percentages.values()) / len(percentages), 1)
    }

# ========== NUEVOS ENDPOINTS ESPECÍFICOS POR POSICIÓN ==========

@app.get("/api/position/{position_key}")
async def get_position_info(position_key: str):
    """Obtiene información de una posición específica"""
    if position_key not in POSITIONS:
        raise HTTPException(status_code=404, detail="Posición no encontrada")
    return POSITIONS[position_key]

@app.get("/api/questions/{test_type}")
async def get_questions(test_type: str, position: Optional[str] = None):
    """Obtiene preguntas de un test específico, opcionalmente validando por posición"""
    if position and position not in POSITIONS:
        raise HTTPException(status_code=400, detail="Posición inválida")
    
    if position and test_type not in POSITIONS[position]["tests"]:
        raise HTTPException(status_code=400, detail=f"Este test no está disponible para la posición {POSITIONS[position]['name']}")
    
    if test_type == "disc":
        return {"questions": [q[0] for q in DISC_QUESTIONS]}
    elif test_type == "big5":
        return {"questions": [q[0] for q in BIG5_QUESTIONS]}
    elif test_type == "mbti":
        return {"questions": [q[0] for q in MBTI_QUESTIONS]}
    elif test_type == "allport":
        return {"questions": [q[0] for q in ALLPORT_QUESTIONS]}
    elif test_type == "terman":
        return {"questions": [q[0] for q in TERMAN_QUESTIONS]}
    elif test_type == "competencias":
        return {"questions": [q[0] for q in COMPETENCIAS_QUESTIONS]}
    else:
        raise HTTPException(status_code=400, detail="Tipo de prueba inválido")

@app.post("/api/submit")
async def submit_test(data: TestAnswers):
    """Envía respuestas de una prueba (ahora con campo position)"""
    # Validar que la posición existe
    if data.position not in POSITIONS:
        raise HTTPException(status_code=400, detail="Posición inválida")
    
    # Validar que el test es apropiado para la posición
    if data.test_type not in POSITIONS[data.position]["tests"]:
        raise HTTPException(status_code=400, detail=f"Este test no está disponible para {POSITIONS[data.position]['name']}")
    
    # Calcular resultados según el tipo de test
    if data.test_type == "disc":
        if len(data.answers) != len(DISC_QUESTIONS):
            raise HTTPException(status_code=400, detail="Número inválido de respuestas")
        result = calculate_disc(data.answers)
    elif data.test_type == "big5":
        if len(data.answers) != len(BIG5_QUESTIONS):
            raise HTTPException(status_code=400, detail="Número inválido de respuestas")
        result = calculate_big5(data.answers)
    elif data.test_type == "mbti":
        if len(data.answers) != len(MBTI_QUESTIONS):
            raise HTTPException(status_code=400, detail="Número inválido de respuestas")
        result = calculate_mbti(data.answers)
    elif data.test_type == "allport":
        if len(data.answers) != len(ALLPORT_QUESTIONS):
            raise HTTPException(status_code=400, detail="Número inválido de respuestas")
        result = calculate_allport(data.answers)
    elif data.test_type == "terman":
        if len(data.answers) != len(TERMAN_QUESTIONS):
            raise HTTPException(status_code=400, detail="Número inválido de respuestas")
        result = calculate_terman(data.answers)
    elif data.test_type == "competencias":
        if len(data.answers) != len(COMPETENCIAS_QUESTIONS):
            raise HTTPException(status_code=400, detail="Número inválido de respuestas")
        result = calculate_competencias(data.answers)
    else:
        raise HTTPException(status_code=400, detail="Tipo de prueba inválido")
    
    # Guardar en Supabase con el campo position
    participant_data = {
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "position": data.position,  # NUEVO: campo position
        "test_type": data.test_type,
        "submitted_at": datetime.utcnow().isoformat()
    }
    
    try:
        participant = await save_to_supabase("participants", participant_data)
        participant_id = participant[0]["id"]
        
        # Guardar respuestas
        answers_data = {
            "participant_id": participant_id,
            "answers": data.answers,
            "test_type": data.test_type
        }
        await save_to_supabase("answers", answers_data)
        
        # Guardar resultados
        if data.test_type == "mbti":
            results_data = {
                "participant_id": participant_id,
                "test_type": data.test_type,
                "scores": result["dimensions"],
                "percentages": result["percentages"],
                "dominant_trait": result["type"],
                "description": result["description"]
            }
        elif data.test_type == "allport":
            results_data = {
                "participant_id": participant_id,
                "test_type": data.test_type,
                "scores": result["scores"],
                "percentages": result["percentages"],
                "dominant_trait": result["dominant"],
                "description": result["description"]
            }
        elif data.test_type == "terman":
            results_data = {
                "participant_id": participant_id,
                "test_type": data.test_type,
                "scores": result["scores"],
                "percentages": result["percentages"],
                "dominant_trait": f"CI: {result['ci_estimate']}",
                "description": result["interpretation"]
            }
        elif data.test_type == "competencias":
            top_comp = result["top_3"][0][0] if result["top_3"] else "N/A"
            results_data = {
                "participant_id": participant_id,
                "test_type": data.test_type,
                "scores": result["scores"],
                "percentages": result["percentages"],
                "dominant_trait": top_comp,
                "description": f"Promedio general: {result['promedio_general']}%"
            }
        else:
            results_data = {
                "participant_id": participant_id,
                "test_type": data.test_type,
                "scores": result["scores"],
                "percentages": result["percentages"],
                "dominant_trait": result.get("dominant", result.get("type", "")),
                "description": result.get("description", "")
            }
        await save_to_supabase("results", results_data)
        
    except Exception as e:
        print(f"Error guardando en Supabase: {e}")
        # Continuar incluso si falla Supabase
    
    return {
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "position": data.position,
        "test_type": data.test_type,
        "results": result
    }

@app.get("/api/participants")
async def get_participants(position: Optional[str] = None):
    """Obtiene todos los participantes, opcionalmente filtrados por posición"""
    async with httpx.AsyncClient() as client:
        url = f"{SUPABASE_URL}/rest/v1/participants?select=*,results(*)"
        
        if position:
            if position not in POSITIONS:
                raise HTTPException(status_code=400, detail="Posición inválida")
            url += f"&position=eq.{position}"
        
        response = await client.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=500, detail="Error obteniendo participantes")

# ========== ENDPOINTS DE LANDING PAGES POR POSICIÓN ==========

@app.get("/almacen", response_class=HTMLResponse)
async def almacen_page():
    """Página de evaluación para posición de Almacén"""
    try:
        with open("almacen.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Página no encontrada")

@app.get("/ventas-mostrador", response_class=HTMLResponse)
async def ventas_mostrador_page():
    """Página de evaluación para posición de Ventas a Mostrador"""
    try:
        with open("ventas_mostrador.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Página no encontrada")

@app.get("/pueblaventas", response_class=HTMLResponse)
async def pueblaventas_page():
    """Página de evaluación para posición de Ventas Puebla"""
    try:
        with open("pueblaventas.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Página no encontrada")

@app.get("/api/status")
async def get_status():
    return {"status": "ok", "version": "1.0"}

# ========== ENDPOINTS ORIGINALES ==========

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
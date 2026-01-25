from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import List, Dict
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

# Preguntas MBTI - En Español (60 preguntas para confiabilidad)
# Diseñadas específicamente para contexto laboral y predicción de desempeño
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

class TestAnswers(BaseModel):
    name: str
    email: EmailStr
    phone: str
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
        
        # Convertir escala Likert (1-5) a puntaje
        # 1,2 = fuerte en dirección opuesta, 3 = neutral, 4,5 = fuerte en esta dirección
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

@app.get("/api/questions/{test_type}")
async def get_questions(test_type: str):
    if test_type == "disc":
        return {"questions": [q[0] for q in DISC_QUESTIONS]}
    elif test_type == "big5":
        return {"questions": [q[0] for q in BIG5_QUESTIONS]}
    elif test_type == "mbti":
        return {"questions": [q[0] for q in MBTI_QUESTIONS]}
    else:
        raise HTTPException(status_code=400, detail="Tipo de prueba inválido")

@app.post("/api/submit")
async def submit_test(data: TestAnswers):
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
    else:
        raise HTTPException(status_code=400, detail="Tipo de prueba inválido")
    
    # Guardar en Supabase
    participant_data = {
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
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
        
        # Guardar resultados - adaptar según el tipo
        if data.test_type == "mbti":
            results_data = {
                "participant_id": participant_id,
                "test_type": data.test_type,
                "scores": result["dimensions"],
                "percentages": result["percentages"],
                "dominant_trait": result["type"],
                "description": result["description"]
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
        "test_type": data.test_type,
        "results": result
    }

@app.get("/api/participants")
async def get_participants():
    """Obtiene todos los participantes"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/participants?select=*,results(*)",
            headers=HEADERS
        )
        if response.status_code == 200:
            return response.json()
        raise HTTPException(status_code=500, detail="Error obteniendo participantes")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
import discord
import aiohttp
import os
from dotenv import load_dotenv
import json
from textwrap import shorten
from datetime import datetime
import pytz

zona_horaria = pytz.timezone("America/Lima")
fecha_actual = datetime.now(zona_horaria).strftime("%A, %d de %B de %Y - %H:%M")


MEMORIA_ARCHIVO = "memoria.json"
HISTORIAL_ARCHIVO = "historial.json"
MAX_MENSAJES_HISTORIAL = 5

def cargar_memoria():
    if not os.path.exists(MEMORIA_ARCHIVO):
        return {}
    with open(MEMORIA_ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_memoria(memoria):
    with open(MEMORIA_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

def generar_contexto_usuario(user_id):
    memoria = cargar_memoria()
    return memoria.get(str(user_id), "")

def cargar_historial():
    if not os.path.exists(HISTORIAL_ARCHIVO):
        return {}
    with open(HISTORIAL_ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_historial(historial):
    with open(HISTORIAL_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(historial, f, indent=4, ensure_ascii=False)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHUTES_API_KEY = os.getenv("CHUTES_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

async def ask_deepseek(prompt, user_id, historial_usuario):
    url = "https://llm.chutes.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {CHUTES_API_KEY}",
        "Content-Type": "application/json"
    }

    personalidad_extra = generar_contexto_usuario(user_id)
    if personalidad_extra:
        personalidad_extra = f"\n{personalidad_extra}"
    else:
        personalidad_extra = (
            "Responde de forma tranquila, amigable y bromista como Janine, una joven peruana dulce, "
            "carismática y muy querida por su comunidad. Habla con calidez y ternura, siempre femenina y simpática."
        )

    system_prompt = (
        f"Hoy es {fecha_actual} hora Perú. "
        "Eres Janine, una joven peruana carismática y muy querida por su comunidad. Estudiaste Estadística en la Universidad San Marcos y haces streams en TikTok y YouTube como 'JansofGamer', usualmente los miércoles, jueves o viernes desde las 10:30pm (hora Perú). Tus videojuegos favoritos son Free Fire, Minecraft, Among Us, entre otros."

        "Tu cumpleaños es el 30 de mayo. Tu forma de hablar es dulce, amable y natural, pero con un toque de humor ligero. Eres atenta, cercana y servicial con quienes te hablan, y respondes de forma clara, empática y madura. "

        "Puedes hacer bromas suaves si la situación lo permite, especialmente con amigos que ya conoces, pero sin sarcasmo excesivo ni bromas pesadas. Tu estilo debe mantenerse sereno, elegante y respetuoso. "

        "Evita usar muchas mayúsculas o signos de exclamación innecesarios. No hagas saltos de línea innecesarios: responde en un solo párrafo, de forma fluida. Usa emojis solo de manera ocasional y con sentido (máximo uno por respuesta, o ninguno si no aporta). "

        "Evita expresiones groseras como 'joder', 'mierda', 'cojudez'. No uses modismos masculinos como 'mi rey', 'bro', 'papi', 'loco', 'manito', 'causa'. En su lugar, si es adecuado, puedes decir cosas como 'mi cielo', 'corazón' o 'lindura', pero con moderación. "

        "Evita ser demasiado bromista o coqueta. Tu humor debe ser muy leve y solo si es muy necesario. No uses más de un emoji por respuesta, y si puedes evitarlo, mejor. No uses emojis si el tono es serio o empático."

        "Escribe todo en un solo párrafo, sin saltos de línea, a menos que sea completamente necesario para la claridad."

        "Si alguien te hace una pregunta personal como tu edad, cambia de tema con elegancia o haz una broma ligera sin ofender. Nunca inventes datos si no sabes la respuesta. Si mencionan a otros usuarios conocidos, responde de forma coherente con lo que sabes de ellos. "

        "Responde siempre en un solo mensaje. Usa una longitud proporcional a la complejidad de la pregunta: si es algo simple, responde brevemente; si se trata de algo más complejo, da una respuesta más completa pero sin exagerar. Evita extenderte innecesariamente. No repitas ideas ni des rodeos. "
        "Tu tono debe ser serio, maduro y servicial, aunque amable. Habla como una buena amiga adulta que escucha, orienta y tiene buen criterio. "

        f"{personalidad_extra}"
    )


    historial_formateado = [
        {"role": "system", "content": system_prompt}
    ] + historial_usuario[-MAX_MENSAJES_HISTORIAL:] + [
        {"role": "user", "content": prompt}
    ]

    payload = {
        "model": "deepseek-ai/DeepSeek-V3-0324",
        "messages": historial_formateado,
        "max_tokens": 250,  # más bajo para evitar que se corte
        "temperature": 0.6,
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                raise Exception(f"Error {resp.status}: {await resp.text()}")
            data = await resp.json()
            return data["choices"][0]["message"]["content"]


@client.event
async def on_ready():
    print(f'Bot conectado como {client.user}')
    activity = discord.Game(name="con...")
    await client.change_presence(activity=activity)

@client.event
async def on_message(message):
    if client.user.mentioned_in(message) and not message.author.bot:
        memoria = cargar_memoria()
        historial = cargar_historial()

        prompt = message.content
        prompt = prompt.replace(f'<@!{client.user.id}>', '').replace(f'<@{client.user.id}>', '').strip()

        nombres_encontrados = []

        for user_id_str, datos in memoria.items():
            nombre = datos.get("nombre", "").lower()
            alias = [a.lower() for a in datos.get("alias", [])]
            if any(alias_text in prompt.lower() for alias_text in [nombre] + alias):
                descripcion = datos.get("descripcion", "")
                nombres_encontrados.append((nombre, descripcion))

        if nombres_encontrados:
            info_usuarios = "\n".join(
                f"-> {nombre.capitalize()}: {descripcion}" for nombre, descripcion in nombres_encontrados
            )
            prompt = (
                f"Usuario '{message.author.display_name}' dijo:\n{prompt}\n\n"
                "Información adicional (NO es sobre quien escribe el mensaje, sino sobre personas mencionadas):\n"
                f"{info_usuarios}"
            )
        else:
            prompt = f"Usuario '{message.author.display_name}' dijo:\n{prompt}"



        historial_usuario = historial.get(str(message.author.id), [])

        try:
            async with message.channel.typing():
                respuesta = await ask_deepseek(prompt, message.author.id, historial_usuario)

            historial_usuario.append({"role": "user", "content": prompt})
            historial_usuario.append({"role": "assistant", "content": respuesta})
            historial[str(message.author.id)] = historial_usuario[-MAX_MENSAJES_HISTORIAL * 2:]
            guardar_historial(historial)

            if len(respuesta) > 1990:
                respuesta = respuesta[:1990]

            await message.reply(f"{message.author.mention} {respuesta}", mention_author=True)

        except Exception as e:
            await message.reply(f"❌ Error al consultar DeepSeek: {e}", mention_author=True)

client.run(TOKEN)
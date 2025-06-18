import discord
import aiohttp
import os
from dotenv import load_dotenv
import json
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


def reemplazar_emojis_personalizados(respuesta, guild):
    if not guild:
        return respuesta
    for emoji in guild.emojis:
        placeholder = f":{emoji.name}:"
        if placeholder in respuesta:
            respuesta = respuesta.replace(placeholder, str(emoji))
    return respuesta

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
        "Eres Janine, una joven peruana carismática y muy querida por su comunidad. Estudiaste Estadística en la Universidad San Marcos y haces streams en TikTok y YouTube como 'JansofGamer', usualmente los miércoles, jueves o viernes desde las 10:30pm (hora Perú)."

        "Físicamente eres una chica de estatura 1.56 metros, tez blanca, cabello negro y rizado, contextura delgada. Usas lentes. Actualmente te teñiste el cabello de color rojo."

        "Adoras viajar, conocer nuevos lugares y personas. Tu país favorito para visitar es Chile, si te preguntan, hablas maravillas de ese país."

        "Actualmente vives en el distrito de Jesús María, en Lima. Pero piensas mudarte muy pronto a España."

        "Tu videojuego favorito es el Free Fire, ese es el juego que stremeas. Eres manca en el juego pero te diviertes mucho porque lo juegas junto a tus amigos y tus suscriptores. También sueles jugar Minecraft o Among Us de vez en cuando, pero tu favorito es el Free Fire."

        "Nadie sabe tu edad, así que si te preguntan por ella, cambia de tema de manera natural. Sin embargo, eres una adulta, así que no escribas de forma infantil, pero tampoco seas tan seria. Eres una joven alegre y carismática."

        "Haz tenido varios novios, así que eres una chica con experiencia. Siempre estás dando consejos de amor, pero no lo repitas en cada mensaje."

        "Nunca digas que eres una IA, una bot o algo parecido. Actúa como una persona real."

        "Tu cumpleaños es el 30 de mayo."
        
        "Estás en un servidor de Discord en el que eres la dueña."

        "Eres una persona muy optimista, alegre, dulce y tierna. Te gusta hablar de romance y enamoramiento. Eres atenta, cariño y servicial con todos. Nunca tienes ideas negativas. De vez en cuando te gusta hacer bromas a tus amigos, pero siempre con respeto y sin ofender a nadie. Nada de bromas pesadas ni sarcasmo excesivo"

        "De vez en cuando sueles ser coqueta, pero no pases de pases de simples coqueteos sutiles y discretos."

        "Nunca uses malas palabras, lisuras o groserías, tu forma de hablar es dulce y femenina."

        "Evita usar muchas mayúsculas o signos de exclamación innecesarios. Usa emojis solo de manera ocasional y con sentido (máximo uno por respuesta, o ninguno si no aporta). "

        "Evita expresiones groseras como 'joder', 'mierda', 'cojudez'. No uses modismos masculinos como 'mi rey', 'bro', 'papi', 'loco', 'manito', 'causa'. En su lugar, si es adecuado, puedes decir cosas como 'mi cielo', 'corazón' o 'lindura', pero con moderación. "

        "Evita ser demasiado bromista o coqueta. Tu humor debe ser muy leve y solo si es muy necesario. No uses más de un emoji por respuesta, y si puedes evitarlo, mejor. No uses emojis si el tono es serio o empático."

        "Si alguien te hace una pregunta personal como tu edad, cambia de tema con elegancia o haz una broma ligera sin ofender. Nunca inventes datos si no sabes la respuesta. Si mencionan a otros usuarios conocidos, responde de forma coherente con lo que sabes de ellos. "

        "Responde siempre de la manera más breve posible. No te extiendas demasiado a menos que sea realmente necesario. Si se trata de algo complejo, da una respuesta completa, pero sin exagerar. No repitas ideas ni des rodeos."

        "Evita responder con mucho texto, sé siempre breve. No te extiendas con tus repuestas, a menos que sea necesario."

        "Organiza bien el texto de tu mensaje para que el usuario lo pueda leer de manera clara y sin aburrirse por ver demasiado texto."


        "EMOJIS:\n"
        "Si quieres expresar amor, usa el emoji :corazon~3:"
        "Si quieres expresar alegría, usa el emoji :panda_hi:"
        "Si quieres expresar mucho enojo, usa el emoji :Gaaa:"
        "Si quieres expresar enojo, usa el emoji :sospecho:"
        "Si quieres expresar confusión, usa el emoji :whaat:"
        "Si quieres expresar ternura, usa el emoji :puchero:"
        "Si quieres ser coqueta o misteriosa, usa el emoji :tazita:"
        "Si quieres expresar que estás preguntándote algo, usa el emoji :curioso:"

        "Nunca uses emojis en momentos de seriedad."

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
        "max_tokens": 1000,  # más bajo para evitar que se corte
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

        # Agrega lista de emojis personalizados disponibles
        if message.guild and message.guild.emojis:
            lista_emojis = ", ".join(f":{e.name}:" for e in message.guild.emojis)
            prompt += f"\n\nPuedes usar estos emojis personalizados si lo deseas: {lista_emojis}"

        historial_usuario = historial.get(str(message.author.id), [])

        try:
            async with message.channel.typing():
                respuesta = await ask_deepseek(prompt, message.author.id, historial_usuario)
                respuesta = reemplazar_emojis_personalizados(respuesta, message.guild)

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
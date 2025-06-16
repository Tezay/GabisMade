import discord
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
raw_channel_id = os.environ.get('DISCORD_CHANNEL_ID')
CHANNEL_ID = int(raw_channel_id) if raw_channel_id and raw_channel_id.isdigit() else 0

async def send_message_async_logic(embed_data):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("Discord Error: BOT_TOKEN or CHANNEL_ID is not configured correctly.")
        return

    intents = discord.Intents.default()

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'Discord Bot logged in as {client.user} to send a message.')
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            try:
                # Crée l'embed à partir des données fournies
                embed = discord.Embed.from_dict(embed_data)
                await channel.send(embed=embed)
                print(f"Discord message sent to channel {CHANNEL_ID}")
            except discord.Forbidden:
                print(f"Discord Error: Bot does not have permissions to send messages to channel {CHANNEL_ID}.")
            except discord.HTTPException as e:
                print(f"Discord Error: Failed to send message. Status: {e.status}, Code: {e.code}, Message: {e.text}")
            except Exception as e:
                print(f"Discord Error: An unexpected error occurred: {e}")
        else:
            print(f"Discord Error: Could not find channel with ID {CHANNEL_ID}. Bot might not be in the server or channel is invalid.")
        await client.close()
        print("Discord Bot logged out.")

    try:
        await client.start(BOT_TOKEN)
    except discord.LoginFailure:
        print("Discord Error: Login failed. Check the BOT_TOKEN.")
    except Exception as e:
        print(f"Discord Error: An error occurred during bot operation: {e}")

def send_discord_notification(order, user, user_phone_number, order_items_details, pickup_slot):

    if not BOT_TOKEN or not CHANNEL_ID:
        print("Discord notification not sent: Missing or invalid BOT_TOKEN or CHANNEL_ID in .env")
        return

    # Prépare les données de l'embed sous forme de dict
    embed_data = {
        "title": "🎉 Nouvelle commande passée !",
        "description": "Une commande a été passée sur GabisMade.",
        "color": discord.Color.blue().value, # Changed color for confirmed order
        "fields": [
            {"name": "🧾 Numéro de Commande", "value": str(order.order_number), "inline": False},
            {"name": "👤 Utilisateur", "value": f"{user.first_name} {user.last_name}", "inline": False},
            {"name": "📞 Téléphone", "value": user_phone_number, "inline": False},
            {"name": "💶 Prix Total", "value": f"{order.total_price:.2f}€", "inline": False}
        ],
        "footer": {"text": f"Commande passée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}"} # Use current time for confirmation
    }

    # Ajoute les informations de retrait si disponibles
    if pickup_slot:
        paris_tz = discord.utils.utcnow().astimezone().tzinfo # Or pytz.timezone('Europe/Paris')
        local_slot_datetime = pickup_slot.slot_datetime.astimezone(paris_tz)

        embed_data["fields"].extend([
            {"name": "🗓️ Créneau de Retrait", 
            "value": local_slot_datetime.strftime('%A %d %B %Y à %Hh%M').capitalize(), 
            "inline": True},
            {"name": "📍 Lieu de Retrait", "value": str(pickup_slot.location), "inline": True}
        ])

    # Ajoute les détails des articles de la commande
    items_str = ""
    if order_items_details:
        for item_detail in order_items_details:
            items_str += f"- {item_detail['name']} (x{item_detail['quantity']}) - {item_detail['price_at_purchase']:.2f}€\n"
    else:
        items_str = "Aucun article."
    embed_data["fields"].append({"name": "🛒 Articles", "value": items_str, "inline": False})


    # Code asynchrone pour envoyer le message Discord
    try:
        # Vérifie si une boucle d'événements asyncio est déjà en cours
        asyncio.get_running_loop()
        # Si une boucle est en cours, on crée une tâche asynchrone
        asyncio.create_task(send_message_async_logic(embed_data))
        print("Discord notification task created for existing event loop.")
    except RuntimeError: # Si aucune boucle n'est en cours, on utilise asyncio.run
        try:
            asyncio.run(send_message_async_logic(embed_data))
            print("Discord notification sent using asyncio.run().")
        except RuntimeError as e_run:
            print(f"Discord Error: asyncio.run() failed: {e_run}. Attempting new loop.")
            # Fallback: créer une nouvelle boucle
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(send_message_async_logic(embed_data))
            finally:
                loop.close()
                asyncio.set_event_loop(None)
            print("Discord notification sent using a manually managed new event loop.")
    except Exception as e:
        print(f"Discord Error: General error in send_discord_notification: {e}")
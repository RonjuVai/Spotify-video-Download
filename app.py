import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SpotifySearchBot:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.api_url = "https://okatsu-rolezapiiz.vercel.app/search/spotify?q="
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Start command with beautiful design"""
        user = update.effective_user
        welcome_text = f"""
🎵 *স্বাগতম {user.first_name}!* 🎵

আমি একটি *Spotify Search Bot* 🤖  
আপনি যে কোনো গান, আর্টিস্ট বা অ্যালবাম সার্চ করতে পারেন!

*কিভাবে ব্যবহার করবেন:*  
1. সরাসরি গানের নাম লিখুন  
2. অথবা /search কমান্ড ব্যবহার করুন  
3. অথবা ইনলাইন মোড ব্যবহার করুন

*উদাহরণ:*  
`/search Shape of You`  
বা শুধু লিখুন `Shape of You`
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 সার্চ শুরু করুন", switch_inline_query_current_chat="")],
            [InlineKeyboardButton("📚 হেল্প", callback_data="help"), 
             InlineKeyboardButton("ℹ️关于", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Help command"""
        help_text = """
*🆘 সাহায্য কেন্দ্র*

*কমান্ড লিস্ট:*
/start - বট শুরু করুন
/search <query> - গান সার্চ করুন
/help - এই মেসেজ দেখান

*সার্চ উদাহরণ:*
• Ed Sheeran
• Shape of You
• Blinding Lights
• Coldplay Adventure of a Lifetime

*ফিচারস:*
✅ 24/7 একটিভ
✅ ফাস্ট সার্চ
✅ হাই কুয়ালিটি স্ট্রিম
✅ ইউজার ফ্রেন্ডলি
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def handle_search(self, update: Update, context: CallbackContext) -> None:
        """Handle search queries"""
        query = ' '.join(context.args) if context.args else None
        
        if not query:
            if update.message.text and not update.message.text.startswith('/'):
                query = update.message.text
            else:
                await update.message.reply_text(
                    "❌ *ইনপুট প্রয়োজন*\n\nসার্চ করতে গানের নাম লিখুন:\n\nউদাহরণ: `/search Shape of You`",
                    parse_mode='Markdown'
                )
                return
        
        await self.perform_search(update, query)

    async def perform_search(self, update: Update, query: str) -> None:
        """Perform actual search and send results"""
        try:
            # Show searching message
            searching_msg = await update.message.reply_text(
                f"🔍 *Searching for:* `{query}`\n\n⏳ Please wait...",
                parse_mode='Markdown'
            )
            
            # Make API request
            response = requests.get(f"{self.api_url}{query}")
            
            if response.status_code == 200:
                data = response.json()
                await self.send_results(update, data, query, searching_msg)
            else:
                await searching_msg.edit_text(
                    "❌ *Search Failed*\n\nসার্ভারে সমস্যা হচ্ছে। পরে আবার চেষ্টা করুন।",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            await update.message.reply_text(
                "❌ *Error Occurred*\n\nদুঃখিত, কোনো সমস্যা হয়েছে। আবার চেষ্টা করুন।",
                parse_mode='Markdown'
            )

    async def send_results(self, update: Update, data: dict, query: str, searching_msg) -> None:
        """Send formatted results"""
        if not data or 'tracks' not in data or not data['tracks']:
            await searching_msg.edit_text(
                f"❌ *No Results Found*\n\n`{query}` - এর জন্য কোনো রেজাল্ট পাওয়া যায়নি।\n\nভিন্ন নামে আবার চেষ্টা করুন।",
                parse_mode='Markdown'
            )
            return

        tracks = data['tracks'][:5]  # Show first 5 results
        
        results_text = f"🎵 *Search Results for:* `{query}`\n\n"
        results_text += f"📊 *Found {len(tracks)} results*\n\n"
        
        keyboard = []
        
        for i, track in enumerate(tracks, 1):
            name = track.get('name', 'Unknown')
            artist = track.get('artist', 'Unknown Artist')
            album = track.get('album', 'Unknown Album')
            
            results_text += f"*{i}. {name}*\n"
            results_text += f"   👤 {artist}\n"
            results_text += f"   💿 {album}\n\n"
            
            # Add button for each track
            keyboard.append([InlineKeyboardButton(
                f"🎵 {i}. {name[:20]}...", 
                callback_data=f"track_{i}"
            )])
        
        # Add additional buttons
        keyboard.append([
            InlineKeyboardButton("🔍 New Search", switch_inline_query_current_chat=""),
            InlineKeyboardButton("📞 Support", url="https://t.me/your_support")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await searching_msg.edit_text(
            results_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def button_handler(self, update: Update, context: CallbackContext) -> None:
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "help":
            await self.help_command(update, context)
        elif data == "about":
            about_text = """
*ℹ️ About This Bot*

*Spotify Search Bot*  
Version: 1.0  
Developer: Your Name  
API: Spotify Search API

*Features:*
• Fast music search
• High quality streaming
• User-friendly interface
• 24/7 availability

*Contact:* @your_username
            """
            await query.edit_message_text(about_text, parse_mode='Markdown')
        elif data.startswith("track_"):
            track_num = int(data.split("_")[1])
            await query.edit_message_text(
                f"🎵 *Track {track_num} Selected*\n\nএই ফিচারটি শীঘ্রই আসছে!",
                parse_mode='Markdown'
            )

    async def inline_query(self, update: Update, context: CallbackContext) -> None:
        """Handle inline queries"""
        query = update.inline_query.query
        
        if not query:
            return
        
        # You can implement inline search here
        results = []
        await update.inline_query.answer(results)

    def run(self):
        """Run the bot"""
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("search", self.handle_search))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_search))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Start the bot
        print("🤖 Bot is running...")
        application.run_polling()

if __name__ == "__main__":
    bot = SpotifySearchBot()
    bot.run()
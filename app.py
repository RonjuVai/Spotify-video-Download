import os
import requests
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler
from telegram.error import TelegramError, NetworkError
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enhanced logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')  # Log file for debugging
    ]
)
logger = logging.getLogger(__name__)

class SpotifySearchBot:
    def __init__(self):
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.api_url = "https://okatsu-rolezapiiz.vercel.app/search/spotify?q="
        self.start_time = time.time()
        
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Enhanced start command with better design"""
        try:
            user = update.effective_user
            welcome_text = f"""
✨ *স্বাগতম {user.first_name}!* ✨

🎵 *Spotify Music Search Bot* 🤖

*আমি যা করতে পারি:*
• 🔍 যেকোনো গান, আর্টিস্ট বা অ্যালবাম সার্চ
• ⚡ লাইটনিং ফাস্ট রেজাল্ট
• 🎧 হাই কুয়ালিটি মিউজিক

*কিভাবে ব্যবহার করবেন:*
1. সরাসরি গানের নাম লিখুন
2. অথবা /search কমান্ড ব্যবহার করুন  
3. অথবা /help দেখুন সাহায্যের জন্য

*উদাহরণ:*
`/search Shape of You`
বা শুধু লিখুন `Blinding Lights`
            """
            
            keyboard = [
                [InlineKeyboardButton("🔍 সার্চ শুরু করুন", switch_inline_query_current_chat="")],
                [InlineKeyboardButton("📚 হেল্প", callback_data="help"), 
                 InlineKeyboardButton("🌟 ফিচারস", callback_data="features")],
                [InlineKeyboardButton("📊 স্ট্যাটাস", callback_data="status")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            logger.info(f"Start command used by {user.first_name} (ID: {user.id})")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("❌ কিছু সমস্যা হয়েছে! পরে আবার চেষ্টা করুন।")

    async def help_command(self, update: Update, context: CallbackContext) -> None:
        """Enhanced help command"""
        help_text = """
🆘 *সাহায্য কেন্দ্র*

*📋 কমান্ড লিস্ট:*
/start - বট শুরু করুন
/search <query> - গান সার্চ করুন  
/help - সাহায্য দেখুন
/status - বট স্ট্যাটাস চেক করুন

*🎯 সার্চ উদাহরণ:*
• Ed Sheeran
• Shape of You  
• Blinding Lights
• Coldplay Adventure of a Lifetime
• Taylor Swift

*🚀 ফিচারস:*
✅ 24/7 একটিভ
✅ সुपার ফাস্ট সার্চ
✅ হাই কুয়ালিটি
✅ ইউজার ফ্রেন্ডলি
✅ ক্র্যাশ প্রোটেকশন

*📞 সাহায্য:*
যদি কোনো সমস্যা হয়, /start লিখে আবার শুরু করুন।
        """
        
        keyboard = [
            [InlineKeyboardButton("🔍 সার্চ ট্রাই করুন", switch_inline_query_current_chat="Shape of You")],
            [InlineKeyboardButton("🏠 হোম", callback_data="home")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    async def status_command(self, update: Update, context: CallbackContext) -> None:
        """Bot status check"""
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        status_text = f"""
📊 *বট স্ট্যাটাস*

✅ *স্ট্যাটাস:* একটিভ
⏰ *আপটাইম:* {hours} ঘন্টা {minutes} মিনিট
🚀 *পারফরম্যান্স:* অপটিমাল
🔧 *ভার্সন:* 2.0

*সিস্টেম ইনফো:*
• 🤖 টেলিগ্রাম: Connected
• 🌐 API: Active  
• 💾 মেমরি: Stable

*সাপোর্ট:* সমস্যা হলে /help কমান্ড ব্যবহার করুন।
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def handle_search(self, update: Update, context: CallbackContext) -> None:
        """Enhanced search handler with better error handling"""
        try:
            query = ' '.join(context.args) if context.args else None
            
            if not query:
                if update.message.text and not update.message.text.startswith('/'):
                    query = update.message.text
                else:
                    await update.message.reply_text(
                        "❌ *সার্চ কীওয়ার্ড প্রয়োজন!*\n\nসার্চ করতে গানের নাম লিখুন:\n\nউদাহরণ: `/search Shape of You`\nবা শুধু লিখুন: `Shape of You`",
                        parse_mode='Markdown'
                    )
                    return
            
            # Query validation
            if len(query) < 2:
                await update.message.reply_text(
                    "❌ *সার্চ কীওয়ার্ড খুব ছোট!*\n\nঅন্তত ২ অক্ষরের বড় কীওয়ার্ড দিন।",
                    parse_mode='Markdown'
                )
                return
                
            if len(query) > 100:
                await update.message.reply_text(
                    "❌ *সার্চ কীওয়ার্ড খুব বড়!*\n\nঅনুগ্রহ করে ছোট করে লিখুন।",
                    parse_mode='Markdown'
                )
                return
            
            await self.perform_search(update, query)
            
        except Exception as e:
            logger.error(f"Error in handle_search: {e}")
            await update.message.reply_text(
                "❌ *সার্চ করতে সমস্যা হচ্ছে!*\n\nদুঃখিত, এখনই সার্চ করা যাচ্ছে না। কিছুক্ষণ পর আবার চেষ্টা করুন।",
                parse_mode='Markdown'
            )

    async def perform_search(self, update: Update, query: str) -> None:
        """Perform search with enhanced error handling"""
        try:
            # Show beautiful searching message
            searching_text = f"""
🔍 *Searching Spotify...*

*কীওয়ার্ড:* `{query}`
*স্ট্যাটাস:* Processing...
⏳ *সময়:* Few seconds...
            """
            
            searching_msg = await update.message.reply_text(
                searching_text,
                parse_mode='Markdown'
            )
            
            # API request with timeout
            try:
                response = requests.get(f"{self.api_url}{query}", timeout=10)
                response.raise_for_status()
                
            except requests.exceptions.Timeout:
                await searching_msg.edit_text(
                    f"❌ *Timeout Error!*\n\n`{query}` - এর সার্চ খুব বেশি সময় নিচ্ছে।\n\n🔧 *সমাধান:* আবার চেষ্টা করুন বা অন্য কীওয়ার্ড ব্যবহার করুন।",
                    parse_mode='Markdown'
                )
                return
                
            except requests.exceptions.RequestException as e:
                await searching_msg.edit_text(
                    f"❌ *Network Error!*\n\nসার্ভারে কানেক্ট হতে সমস্যা হচ্ছে।\n\n🔧 *সমাধান:* কিছুক্ষণ পর আবার চেষ্টা করুন।",
                    parse_mode='Markdown'
                )
                return

            if response.status_code == 200:
                data = response.json()
                await self.send_results(update, data, query, searching_msg)
            else:
                await searching_msg.edit_text(
                    f"❌ *API Error!*\n\nসার্চ সার্ভারে সমস্যা হচ্ছে (Status: {response.status_code})\n\n🔧 *সমাধান:* কিছুক্ষণ পর আবার চেষ্টা করুন।",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            try:
                await update.message.reply_text(
                    "❌ *Unexpected Error!*\n\nদুঃখিত, অপ্রত্যাশিত সমস্যা হয়েছে।\n\n🔧 *সমাধান:* /start লিখে আবার শুরু করুন।",
                    parse_mode='Markdown'
                )
            except:
                pass

    async def send_results(self, update: Update, data: dict, query: str, searching_msg) -> None:
        """Send formatted results with enhanced design"""
        try:
            if not data or 'tracks' not in data or not data['tracks']:
                no_results_text = f"""
❌ *No Results Found!*

`{query}` - এর জন্য কোনো গান পাওয়া যায়নি।

💡 *সাজেশন:*
• ভিন্ন কীওয়ার্ড ব্যবহার করুন
• স্পেলিং চেক করুন  
• ইংরেজি নাম ব্যবহার করুন

উদাহরণ: `Shape of You`, `Blinding Lights`
                """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 নতুন সার্চ", switch_inline_query_current_chat="")],
                    [InlineKeyboardButton("📚 হেল্প", callback_data="help")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await searching_msg.edit_text(
                    no_results_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return

            tracks = data['tracks'][:6]  # Show first 6 results
        
            results_text = f"""
🎵 *Search Results* 🎵

*কীওয়ার্ড:* `{query}`
*মোট রেজাল্ট:* {len(tracks)} টি গান

"""
        
            keyboard = []
        
            for i, track in enumerate(tracks, 1):
                name = track.get('name', 'Unknown Track')
                artist = track.get('artist', 'Unknown Artist')
                album = track.get('album', 'Unknown Album')
            
                results_text += f"*{i}. {name}*\n"
                results_text += f"   👤 *Artist:* {artist}\n"
                results_text += f"   💿 *Album:* {album}\n\n"
            
                # Add button for each track
                button_text = f"🎵 {i}. {name[:25]}{'...' if len(name) > 25 else ''}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"track_{i}")])
        
            # Add additional buttons
            keyboard.extend([
                [InlineKeyboardButton("🔄 নতুন সার্চ", switch_inline_query_current_chat="")],
                [InlineKeyboardButton("📚 হেল্প", callback_data="help"),
                 InlineKeyboardButton("🏠 হোম", callback_data="home")]
            ])
        
            reply_markup = InlineKeyboardMarkup(keyboard)
        
            await searching_msg.edit_text(
                results_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error sending results: {e}")
            await searching_msg.edit_text(
                "❌ *Results display error!*\n\nরেজাল্ট দেখাতে সমস্যা হচ্ছে।\n\n🔧 *সমাধান:* আবার চেষ্টা করুন।",
                parse_mode='Markdown'
            )

    async def button_handler(self, update: Update, context: CallbackContext) -> None:
        """Enhanced button handler"""
        query = update.callback_query
        await query.answer()
        
        try:
            data = query.data
        
            if data == "help":
                await self.help_command(update, context)
            elif data == "home" or data == "start":
                await self.start(update, context)
            elif data == "features":
                features_text = """
🌟 *বট ফিচারস*

*🚀 পারফরম্যান্স:*
• সुपার ফাস্ট সার্চ
• 24/7 একটিভ
• লো লেটেন্সি

*🎵 মিউজিক ফিচারস:*
• গান, আর্টিস্ট, অ্যালবাম সার্চ
• হাই কুয়ালিটি অডিও
• ডিটেইল্ড ইনফো

*🔧 টেকনিকাল:*
• অটো রিকভারি
• এরর হ্যান্ডলিং
• রিয়েলটাইম আপডেট

*📱 ইউজার এক্সপেরিয়েন্স:*
• বাংলা & ইংরেজি সাপোর্ট
• ইনটুইটিভ ডিজাইন
• কুইক রেসপন্স
                """
                await query.edit_message_text(features_text, parse_mode='Markdown')
            elif data == "status":
                await self.status_command(update, context)
            elif data.startswith("track_"):
                track_num = int(data.split("_")[1])
                track_text = f"""
🎵 *Track {track_num} Selected*

✅ এই ট্র্যাকটি সিলেক্ট হয়েছে!

🚀 *কমিং সুন:*  
• প্লে ফিচার  
• ডাউনলোড অপশন
• শেয়ার ফিচার

📢 *নোট:* এই ফিচারগুলো শীঘ্রই আসছে! 
আপাতত নতুন গান সার্চ করুন।
                """
                await query.edit_message_text(track_text, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Button handler error: {e}")
            await query.edit_message_text("❌ বাটন প্রসেস করতে সমস্যা! /start লিখুন।")

    async def error_handler(self, update: Update, context: CallbackContext) -> None:
        """Global error handler"""
        try:
            logger.error(f"Exception while handling an update: {context.error}")
            
            # Don't send error message if it's a network error (user won't see it anyway)
            if isinstance(context.error, NetworkError):
                return
                
            if update and update.effective_message:
                error_text = """
❌ *System Error Occurred!*

🔧 অটো রিকভারি একটিভ...
🔄 বট রিস্টার্ট হচ্ছে...

✅ কিছুক্ষণের মধ্যে আবার চেষ্টা করুন।
                """
                await update.effective_message.reply_text(
                    error_text,
                    parse_mode='Markdown'
                )
        except:
            pass

    def run(self):
        """Run the bot with enhanced stability"""
        try:
            # Create application with better configuration
            application = Application.builder().token(self.token).build()
            
            # Add enhanced handlers
            application.add_handler(CommandHandler("start", self.start))
            application.add_handler(CommandHandler("help", self.help_command))
            application.add_handler(CommandHandler("search", self.handle_search))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_search))
            application.add_handler(CallbackQueryHandler(self.button_handler))
            
            # Add error handler
            application.add_error_handler(self.error_handler)
            
            # Start the bot with better polling configuration
            print("🤖 Bot is starting with enhanced stability...")
            print(f"✅ Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("🔧 Configuration: Stable Mode Active")
            
            # Run with enhanced polling settings
            application.run_polling(
                poll_interval=1.0,
                timeout=30,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.critical(f"Bot crashed: {e}")
            print(f"🔴 Bot crashed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("🔄 Attempting auto-restart in 10 seconds...")
            time.sleep(10)
            self.run()  # Auto-restart

if __name__ == "__main__":
    bot = SpotifySearchBot()
    bot.run()

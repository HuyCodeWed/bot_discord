import discord
from discord import app_commands, ui
import asyncio
import os
from dotenv import load_dotenv
# Đảm bảo bạn có file google_sheets.py với các hàm đã cập nhật
from google_sheets import get_all_accounts, delete_account_by_stt

# Tải các biến môi trường
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID"))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.tree.sync()
        print('Commands synced successfully.')

client = MyClient(intents=intents)

# --- PHẦN UI (SELECT MENU VÀ VIEW) ---
class AccountSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Chọn tài khoản bạn muốn nhận", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Chuyển xử lý sang view chính
        await self.view.handle_selection(interaction, self.values[0])

class AccountSelectView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=300) # Hết hạn sau 5 phút
        self.add_item(AccountSelect(options))

    async def handle_selection(self, interaction: discord.Interaction, stt: str):
        await interaction.response.defer(ephemeral=True) # Cho bot thời gian xử lý

        try:
            found_account = delete_account_by_stt(int(stt))

            if found_account and len(found_account) == 6: # Kiểm tra có đủ 6 cột không
                ticket_category = client.get_channel(TICKET_CATEGORY_ID)
                if not ticket_category:
                    await interaction.followup.send("Lỗi: Không tìm thấy danh mục ticket.", ephemeral=True)
                    return

                channel_name = f"order-{interaction.user.name.lower()}"
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True),
                    interaction.guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(view_channel=True),
                    interaction.guild.me: discord.PermissionOverwrite(view_channel=True)
                }
                new_channel = await ticket_category.create_text_channel(name=channel_name, overwrites=overwrites)

                # THAY ĐỔI Ở ĐÂY: Thêm giá tiền vào tin nhắn ticket
                account_info = (f"**Tài khoản:** `{found_account[1]}`\n"
                                f"**Mật khẩu:** ||`{found_account[2]}`||\n"
                                f"**Level:** `{found_account[3]}`\n"
                                f"**Thời gian cày:** `{found_account[4]}`\n"
                                f"**Giá tiền:** `{found_account[5]}`")

                embed = discord.Embed(title="Thông tin tài khoản của bạn", description=f"{interaction.user.mention}, đây là thông tin tài khoản bạn đã chọn.", color=discord.Color.blue())
                embed.add_field(name="Chi tiết", value=account_info)

                ticket_view = discord.ui.View(timeout=None)
                close_button = discord.ui.Button(label="Đóng Ticket", style=discord.ButtonStyle.red, custom_id=f"close_ticket_{new_channel.id}")

                async def close_callback(button_interaction: discord.Interaction):
                    admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
                    if admin_role in button_interaction.user.roles:
                        await button_interaction.response.send_message("Ticket sẽ bị đóng trong 5 giây...", ephemeral=True)
                        await asyncio.sleep(5)
                        await new_channel.delete()
                    else:
                        await button_interaction.response.send_message("Bạn không có quyền đóng ticket này!", ephemeral=True)

                close_button.callback = close_callback
                ticket_view.add_item(close_button)

                admin_role_mention = interaction.guild.get_role(ADMIN_ROLE_ID).mention
                await new_channel.send(f"{admin_role_mention} {interaction.user.mention}", embed=embed, view=ticket_view)

                await interaction.followup.send(f"Tài khoản của bạn đã được gửi vào kênh {new_channel.mention}. Vui lòng kiểm tra!", ephemeral=True)
            else:
                await interaction.followup.send("Tài khoản này có thể đã được người khác lấy. Vui lòng thử lại.", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"Có lỗi xảy ra: {e}", ephemeral=True)

    async def on_timeout(self):
        # Xóa dropdown khi hết hạn
        if self.message:
            await self.message.delete()


# --- CÁC LỆNH SLASH ---
def is_allowed_role(interaction: discord.Interaction) -> bool:
    role = interaction.guild.get_role(ALLOWED_ROLE_ID)
    return role in interaction.user.roles if role else False

@client.tree.command(name="getacc", description="Lấy một tài khoản từ danh sách")
@app_commands.check(is_allowed_role)
async def getacc_command(interaction: discord.Interaction):
    accounts_list = get_all_accounts()
    options = []

    if not accounts_list:
        await interaction.response.send_message("Hiện không còn tài khoản nào.", ephemeral=True)
        return

    for account in accounts_list:
        if len(account) == 6: # Chỉ xử lý các dòng có đủ 6 cột
            stt, _, _, level, time_limit, price = account
            # THAY ĐỔI Ở ĐÂY: Thêm giá tiền vào description
            options.append(discord.SelectOption(
                label=f"Tài khoản #{stt}",
                description=f"Level: {level} | Hạn cày: {time_limit} | Giá: {price}",
                value=stt
            ))

    if not options:
        await interaction.response.send_message("Không có tài khoản hợp lệ nào để hiển thị.", ephemeral=True)
        return

    embed = discord.Embed(title="Chọn một tài khoản", description="Chào mừng! Dưới đây là danh sách các tài khoản hiện có. Vui lòng chọn một tài khoản từ menu bên dưới.", color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=AccountSelectView(options), ephemeral=True)

@getacc_command.error
async def on_getacc_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("Bạn không có đủ quyền để sử dụng lệnh này.", ephemeral=True)

client.run(TOKEN)
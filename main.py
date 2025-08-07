import discord
from discord import app_commands, ui
import asyncio
import os
from dotenv import load_dotenv
from google_sheets import get_all_accounts, delete_account_by_stt

# Tải các biến môi trường từ tệp .env
load_dotenv()

# Lấy các giá trị từ biến môi trường
TOKEN = os.getenv("BOT_TOKEN")
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID"))
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID"))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))

# Tên file chứa danh sách tài khoản
ACCOUNTS_FILE = "accounts.txt"

# Intents cần thiết để bot hoạt động
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


class AccountSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Chọn tài khoản bạn muốn nhận",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await self.view.select_callback(interaction)

class AccountSelectView(discord.ui.View):
    def __init__(self, options, accounts_list):
        super().__init__(timeout=None)
        self.accounts_list = accounts_list
        self.add_item(AccountSelect(options))

    async def select_callback(self, interaction: discord.Interaction):
        stt = int(self.children[0].values[0])

        try:
            found_account = delete_account_by_stt(stt)

            if found_account:
                ticket_category = client.get_channel(TICKET_CATEGORY_ID)
                if not ticket_category:
                    await interaction.response.send_message("Lỗi: Không tìm thấy danh mục ticket.", ephemeral=True)
                    return

                channel_name = f"order-{interaction.user.name.lower()}"

                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True),
                    interaction.guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(view_channel=True),
                    interaction.guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
                }

                new_channel = await ticket_category.create_text_channel(name=channel_name, overwrites=overwrites)

                account_info = f"**Tài khoản:** `{found_account[1]}`\n" \
                               f"**Mật khẩu:** `{found_account[2]}`\n" \
                               f"**Level:** `{found_account[3]}`\n" \
                               f"**Thời gian cày:** `{found_account[4]}`"

                admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)

                embed = discord.Embed(
                    title="Thông tin tài khoản của bạn",
                    description=f"{interaction.user.mention}, đây là thông tin tài khoản bạn đã chọn.",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Chi tiết", value=account_info)

                ticket_view = discord.ui.View()
                close_button = discord.ui.Button(label="Đóng Ticket", style=discord.ButtonStyle.red)

                async def close_callback(button_interaction: discord.Interaction):
                    if interaction.guild.get_role(ADMIN_ROLE_ID) in button_interaction.user.roles:
                        await button_interaction.response.send_message("Ticket sẽ bị đóng trong 5 giây...", ephemeral=True)
                        await asyncio.sleep(5)
                        try:
                            await new_channel.delete()
                        except discord.Forbidden:
                            await button_interaction.followup.send(
                                "Lỗi: Bot không có quyền xóa kênh. Kiểm tra quyền `Manage Channels`.", ephemeral=True)
                    else:
                        await button_interaction.response.send_message("Bạn không có quyền đóng ticket này!", ephemeral=True)

                close_button.callback = close_callback
                ticket_view.add_item(close_button)

                await new_channel.send(f"{admin_role.mention} {interaction.user.mention}", embed=embed, view=ticket_view)

                await interaction.response.send_message(
                    f"Tài khoản của bạn đã được gửi vào kênh {new_channel.mention}. Vui lòng kiểm tra!",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message("Không tìm thấy tài khoản bạn yêu cầu.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"Có lỗi xảy ra: {e}", ephemeral=True)



async def select_callback(self, interaction: discord.Interaction):
    stt = int(self.children[0].values[0])
    
    try:
        found_account = delete_account_by_stt(stt)

        if found_account:
            ticket_category = client.get_channel(TICKET_CATEGORY_ID)
            if not ticket_category:
                await interaction.response.send_message("Lỗi: Không tìm thấy danh mục ticket.", ephemeral=True)
                return

            channel_name = f"order-{interaction.user.name.lower()}"

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True),
                interaction.guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(view_channel=True),
                interaction.guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
            }

            new_channel = await ticket_category.create_text_channel(name=channel_name, overwrites=overwrites)

            account_info = f"**Tài khoản:** `{found_account[1]}`\n" \
                           f"**Mật khẩu:** `{found_account[2]}`\n" \
                           f"**Level:** `{found_account[3]}`\n" \
                           f"**Thời gian cày:** `{found_account[4]}`"

            admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)

            embed = discord.Embed(
                title="Thông tin tài khoản của bạn",
                description=f"{interaction.user.mention}, đây là thông tin tài khoản bạn đã chọn.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Chi tiết", value=account_info)

            ticket_view = discord.ui.View()
            close_button = discord.ui.Button(label="Đóng Ticket", style=discord.ButtonStyle.red)

            async def close_callback(button_interaction: discord.Interaction):
                if interaction.guild.get_role(ADMIN_ROLE_ID) in button_interaction.user.roles:
                    await button_interaction.response.send_message("Ticket sẽ bị đóng trong 5 giây...", ephemeral=True)
                    await asyncio.sleep(5)
                    try:
                        await new_channel.delete()
                    except discord.Forbidden:
                        await button_interaction.followup.send(
                            "Lỗi: Bot không có quyền xóa kênh. Kiểm tra quyền `Manage Channels`.", ephemeral=True)
                else:
                    await button_interaction.response.send_message("Bạn không có quyền đóng ticket này!", ephemeral=True)

            close_button.callback = close_callback
            ticket_view.add_item(close_button)

            await new_channel.send(f"{admin_role.mention} {interaction.user.mention}", embed=embed, view=ticket_view)

            await interaction.response.send_message(
                f"Tài khoản của bạn đã được gửi vào kênh {new_channel.mention}. Vui lòng kiểm tra!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("Không tìm thấy tài khoản bạn yêu cầu.", ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(f"Có lỗi xảy ra: {e}", ephemeral=True)
def get_accounts_options():
    options = []
    accounts_list = []
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            for line in f.readlines():
                parts = line.strip().split(" | ")
                if len(parts) == 5:
                    stt, tk, mk, level, time_limit = parts
                    options.append(discord.SelectOption(
                        label=f"Tài khoản #{stt}",
                        description=f"Level: {level} | Hạn cày: {time_limit}",
                        value=stt
                    ))
                    accounts_list.append(parts)
    except FileNotFoundError:
        pass
    return options, accounts_list

def is_allowed_role(interaction: discord.Interaction) -> bool:
    role = interaction.guild.get_role(ALLOWED_ROLE_ID)
    if role:
        return role in interaction.user.roles
    return False

@client.tree.command(name="getacc", description="Lấy một tài khoản từ danh sách")
@app_commands.check(is_allowed_role)
async def getacc_command(interaction: discord.Interaction):
    loop = asyncio.get_event_loop()
    options, accounts_list = await loop.run_in_executor(None, get_all_accounts)
    if not options:
        await interaction.response.send_message("Hiện không còn tài khoản nào.", ephemeral=True)
        return
        
    embed = discord.Embed(
        title="Chọn một tài khoản",
        description="Chào mừng! Dưới đây là danh sách các tài khoản hiện có. Vui lòng chọn một tài khoản từ menu bên dưới.",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(
        embed=embed,
        view=AccountSelectView(options, accounts_list),
        ephemeral=True
    )

@getacc_command.error
async def on_getacc_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "Bạn không có đủ quyền để sử dụng lệnh này.",
            ephemeral=True
        )

# Chạy bot
client.run(TOKEN)

import discord
from discord.ext import commands
from logic import DB_Manager
from config import DATABASE, TOKEN

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)
manager = DB_Manager(DATABASE)

# Fungsi event: berjalan ketika bot berhasil online dan siap digunakan
@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

# Fungsi command: perintah pertama untuk memulai bot dan menampilkan info
@bot.command(name='start')
async def start_command(ctx):
    await ctx.send("Halo! Saya adalah bot manajer proyek\nSaya akan membantu kamu menyimpan proyek dan informasi tentangnya!)")
    await info(ctx)  # Memanggil fungsi info untuk menampilkan daftar perintah

# Fungsi command: menampilkan daftar perintah bot
@bot.command(name='info')
async def info(ctx):
    await ctx.send("""
Berikut adalah perintah yang dapat membantu kamu:

!new_project - gunakan untuk menambahkan proyek baru
!projects - gunakan untuk menampilkan semua proyek
!update_projects - gunakan untuk mengubah data proyek
!skills - gunakan untuk menghubungkan keterampilan ke proyek
!delete - gunakan untuk menghapus proyek

Kamu juga dapat memasukkan nama proyek untuk mengetahui informasi tentangnya!""")

# Fungsi command: membuat proyek baru dan menyimpannya ke database
@bot.command(name='new_project')
async def new_project(ctx):
    await ctx.send("Masukkan nama proyek:")

    # Fungsi check untuk memastikan hanya pesan dari user & channel yang sama
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    # Menunggu input nama proyek
    name = await bot.wait_for('message', check=check)
    data = [ctx.author.id, name.content]

    # Meminta link proyek
    await ctx.send("Masukkan link proyek")
    link = await bot.wait_for('message', check=check)
    data.append(link.content)

    # Mengambil daftar status dari database
    statuses = [x[0] for x in manager.get_statuses()]
    await ctx.send("Masukkan status proyek saat ini", delete_after=60.0)
    await ctx.send("\n".join(statuses), delete_after=60.0)

    # Menunggu input status dan validasi
    status = await bot.wait_for('message', check=check)
    if status.content not in statuses:
        await ctx.send("Kamu memilih status yang tidak ada dalam daftar, silakan coba lagi!)", delete_after=60.0)
        return

    # Mendapatkan ID status & menyimpan proyek ke database
    status_id = manager.get_status_id(status.content)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    await ctx.send("Proyek telah disimpan")

# Fungsi command: menampilkan proyek milik user
@bot.command(name='projects')
async def get_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)

    # Jika ada proyek → tampilkan daftar
    if projects:
        text = "\n".join([f"Project name: {x[2]} \nLink: {x[4]}\n" for x in projects])
        await ctx.send(text)
    else:
        # Jika tidak ada proyek
        await ctx.send('Kamu belum memiliki proyek!\nKamu dapat menambahkannya menggunakan perintah !new_project')

# Fungsi command: menambahkan skill ke proyek tertentu
@bot.command(name='skills')
async def skills(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)

    # Cek jika user punya proyek
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send('Pilih proyek yang ingin kamu tambahkan keterampilan')
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        # Memilih proyek
        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('Kamu tidak memiliki proyek tersebut, silakan coba lagi!)')
            return

        # Menampilkan daftar skill
        skills = [x[1] for x in manager.get_skills()]
        await ctx.send('Pilih keterampilan')
        await ctx.send("\n".join(skills))

        # Memilih skill
        skill = await bot.wait_for('message', check=check)
        if skill.content not in skills:
            await ctx.send('Sepertinya kamu memilih keterampilan yang tidak ada dalam daftar, silakan coba lagi!)')
            return

        # Menyimpan relasi skill → proyek di database
        manager.insert_skill(user_id, project_name.content, skill.content)
        await ctx.send(f'Keterampilan {skill.content} telah ditambahkan ke proyek {project_name.content}')
    else:
        await ctx.send('Kamu belum memiliki proyek!\nGunakan !new_project untuk menambahkannya')

# Fungsi command: menghapus proyek user dari database
@bot.command(name='delete')
async def delete_project(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)

    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Pilih proyek yang ingin kamu hapus")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        # Menunggu input proyek untuk dihapus
        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('Kamu tidak memiliki proyek tersebut, silakan coba lagi!')
            return

        # Menghapus proyek berdasarkan ID
        project_id = manager.get_project_id(project_name.content, user_id)
        manager.delete_project(user_id, project_id)
        await ctx.send(f'Proyek {project_name.content} telah dihapus!')
    else:
        await ctx.send('Kamu belum memiliki proyek! Gunakan !new_project untuk menambahkannya')

# Fungsi command: mengubah atribut (nama, deskripsi, link, status) dari proyek
@bot.command(name='update_projects')
async def update_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)

    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Pilih proyek yang ingin kamu ubah")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        # Memilih proyek
        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send("Ada yang salah! Silakan pilih proyek yang ingin kamu ubah lagi:")
            return

        # Memilih atribut yang ingin diperbarui
        await ctx.send("Pilih apa yang ingin kamu ubah dalam proyek")
        attributes = {'Nama proyek': 'project_name', 'Deskripsi': 'description', 'Link': 'url', 'Status': 'status_id'}
        await ctx.send("\n".join(attributes.keys()))

        attribute = await bot.wait_for('message', check=check)
        if attribute.content not in attributes:
            await ctx.send("Sepertinya kamu membuat kesalahan, silakan coba lagi!")
            return

        # Jika atribut status → tampilkan daftar status
        if attribute.content == 'Status':
            statuses = manager.get_statuses()
            await ctx.send("Pilih status baru untuk proyek")
            await ctx.send("\n".join([x[0] for x in statuses]))
            update_info = await bot.wait_for('message', check=check)

            # Validasi status
            if update_info.content not in [x[0] for x in statuses]:
                await ctx.send("Status tidak valid, silakan coba lagi!")
                return

            update_info = manager.get_status_id(update_info.content)

        else:
            # Jika atribut lain → langsung minta input baru
            await ctx.send(f"Masukkan nilai baru untuk {attribute.content}")
            update_info = await bot.wait_for('message', check=check)
            update_info = update_info.content

        # Update database
        manager.update_projects(attributes[attribute.content], (update_info, project_name.content, user_id))
        await ctx.send("Selesai! Pembaruan telah dilakukan!")
    else:
        await ctx.send('Kamu belum memiliki proyek! Gunakan !new_project untuk menambahkannya')

# Menjalankan bot
bot.run(TOKEN)

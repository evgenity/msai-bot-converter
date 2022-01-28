from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine

engine = create_engine('sqlite:///bot-converter.db', echo=True)
Base = declarative_base()


from sqlalchemy import Column, Integer, String
class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    filename = Column(String)

    def __repr__(self):
        return "<File(chat_id='{}', filename='{}')>".format(self.chat_id, self.filename)
    
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    username = Column(String)
    state = Column(String)

    def __repr__(self):
        return "<User(chat_id='{}', username='{}')>".format(self.chat_id, self.filename)

from sqlalchemy import create_engine
engine = create_engine('sqlite:///bot-converter.db', echo=True)
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)


import telebot
from telebot import types

bot = telebot.TeleBot("5069674898:AAGdHYM4cn-ZqQqbhR2vke34ke8qMos1lTY", parse_mode=None)

WELCOME_MSG = "👋 Howdy, how are you doing? \
You can upload video with the following formats: *.avi, *.mov, *.mp4! and I convert them to *.avi, *.mov, *.mp4, *.gif! \
Just upload a short video to me, and then choose file type you want. \
Following commands are avilable: /start, /setname, /help!"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, WELCOME_MSG)
    ed_user = User(chat_id=message.chat.id, state='start')
    session = Session()
    session.add(ed_user)
    session.commit()
    session.close()
    
@bot.message_handler(commands=['setname'])
def set_name(message):
    bot.reply_to(message, 'Set your username')
    session = Session()
    our_user = session.query(User).filter_by(chat_id=message.chat.id).order_by(User.id.desc()).first()
    our_user.state = 'set_name'
    session.commit()
    session.close()

@bot.message_handler(content_types=['video', 'video_note', 'document'])
def handle_docs_video(message):
    print(message.content_type)
    # Get file
    if message.content_type == 'video_note':
        file_info = bot.get_file(message.video_note.file_id)
    elif message.content_type == 'video':
        file_info = bot.get_file(message.video.file_id)
    elif message.content_type == 'document':
        file_info = bot.get_file(message.document.file_id)
    
    ## Check if filetype is supported 
    file_type = file_info.file_path.split('.')[-1].lower()
    if (file_type in ['mov', 'mp4', 'avi']):
        bot.reply_to(message, 'Detected file type: "{}". Congrats! It is supported!'.format(file_type))
    else:
        bot.reply_to(message, 'Detected file type: "{}". Sorry is not supported!'.format(file_type))
    
    ## Save temporary file
    downloaded_file = bot.download_file(file_info.file_path)
    temp_filename = str(file_info.file_path).split('/')[-1]
    with open(temp_filename,'wb') as new_file:
        new_file.write(downloaded_file)
        
    # Get target filetype
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('/avi')
    itembtn2 = types.KeyboardButton('/mov')
    itembtn3 = types.KeyboardButton('/mp4')
    itembtn4 = types.KeyboardButton('/gif')
    
    

    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    bot.send_message(message.chat.id, "Choose the target file type:", reply_markup=markup)
    
    ed_file = File(chat_id=message.chat.id, filename=temp_filename)
    session = Session()
    session.add(ed_file)
    session.commit()
    session.close()

@bot.message_handler(commands=['avi', 'mov', 'mp4', 'gif'])
def process_file(message):
    print('processing file')
    markup = types.ReplyKeyboardRemove(selective=False)
    target_file_type = message.text[1:]
    bot.send_message(message.chat.id, 'You\'ve chosen .{} format! Processing...'.format(target_file_type), reply_markup=markup)
    
    session = Session()
    our_file = session.query(File).filter_by(chat_id=message.chat.id).order_by(File.id.desc()).first()
    session.close()
    
    temp_filename = our_file.filename
    
    # Convert file
    import ffmpeg
    try:
        stream = ffmpeg.input(temp_filename)
        output_name = '{}.{}'.format(temp_filename.split('.')[0], target_file_type)
        stream = ffmpeg.output(stream, output_name)
        ffmpeg.run(stream)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Ooops! An error occured! Try again! {}".format(e))
    
    # Send file
    with open(output_name,'rb') as converted_file:
        session = Session()
        our_user = session.query(User).filter_by(chat_id=message.chat.id).order_by(User.id.desc()).first()
        session.close()
        if our_user.username:
            bot.send_message(message.chat.id, 'Thank you for using our service, {}'.format(our_user.username))
        bot.send_document(message.chat.id, converted_file)
    import os
    os.remove(output_name)

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    session = Session()
    our_user = session.query(User).filter_by(chat_id=message.chat.id).order_by(User.id.desc()).first()
    
    if our_user.state == 'set_name':
        our_user.username = message.text
        our_user.state = 'complete'
        session.commit()
        bot.reply_to(message, 'Hello, {}, uppload a video you want to convert!'.format(our_user.username))
        session.close()
    else:
        bot.reply_to(message, WELCOME_MSG)

bot.infinity_polling()

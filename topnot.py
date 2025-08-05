import streamlit as st
import os
import json
import hashlib
from datetime import datetime

st.set_page_config(page_title="🔐 المفكرة السرية", layout="centered")
st.title("🔐 المفكرة السرية")

BASE_DIR = "vault_users"

# إنشاء مجلد المستخدمين
os.makedirs(BASE_DIR, exist_ok=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_dir(username):
    return os.path.join(BASE_DIR, username)

def save_user(username, password_hash):
    users = load_users()
    users[username] = password_hash
    with open(os.path.join(BASE_DIR, "users.json"), "w") as f:
        json.dump(users, f)

def load_users():
    path = os.path.join(BASE_DIR, "users.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

# ------------ واجهة تسجيل الدخول / الحساب -------------
if "logged_user" not in st.session_state:
    st.session_state.logged_user = None

if not st.session_state.logged_user:
    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب"])
    with tab1:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            users = load_users()
            if username in users and hash_password(password) == users[username]:
                st.session_state.logged_user = username
                st.success(f"مرحباً {username}!")
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
    with tab2:
        new_user = st.text_input("اسم مستخدم جديد")
        new_pass = st.text_input("كلمة مرور جديدة", type="password")
        if st.button("إنشاء الحساب"):
            users = load_users()
            if new_user in users:
                st.warning("اسم المستخدم موجود مسبقاً.")
            elif new_user == "" or new_pass == "":
                st.warning("يرجى ملء الحقول.")
            else:
                save_user(new_user, hash_password(new_pass))
                os.makedirs(get_user_dir(new_user), exist_ok=True)
                st.success("تم إنشاء الحساب! يمكنك تسجيل الدخول الآن.")
    st.stop()

# -------------- الوظائف بعد الدخول --------------
user_dir = get_user_dir(st.session_state.logged_user)
NOTES_DIR = os.path.join(user_dir, "notes")
FILES_DIR = os.path.join(user_dir, "files")
IMAGES_DIR = os.path.join(user_dir, "images")

for folder in [NOTES_DIR, FILES_DIR, IMAGES_DIR]:
    os.makedirs(folder, exist_ok=True)

option = st.sidebar.radio("القسم", ["📝 ملاحظات", "📂 ملفات", "🖼️ صور"])

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_file(path):
    if os.path.exists(path):
        os.remove(path)

# ---------------- 📝 ملاحظات ----------------
if option == "📝 ملاحظات":
    st.header("📒 ملاحظاتك")
    note_files = os.listdir(NOTES_DIR)

    st.markdown("### ➕ إضافة ملاحظة")
    note_title = st.text_input("عنوان الملاحظة")
    note_color = st.color_picker("لون الملاحظة", "#f0f0f0")
    note_content = st.text_area("نص الملاحظة")

    if st.button("حفظ"):
        if note_title and note_content:
            filename = f"{note_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            path = os.path.join(NOTES_DIR, filename)
            save_json(path, {
                "title": note_title,
                "content": note_content,
                "color": note_color,
                "time": str(datetime.now())
            })
            st.success("✅ تم حفظ الملاحظة")
            st.rerun()

    for note_file in note_files:
        path = os.path.join(NOTES_DIR, note_file)
        try:
            note = load_json(path)
        except:
            continue

        with st.expander(f"📌 {note.get('title', '')}"):
            st.markdown(f"<div style='background-color:{note.get('color')}; padding:10px; border-radius:10px;'>"
                        f"<b>عدد الكلمات:</b> {len(note.get('content','').split())}<br>"
                        f"<b>تاريخ:</b> {note.get('time', '')}<br><br>"
                        f"{note.get('content', '')}</div>", unsafe_allow_html=True)

            with st.popover("⋮ خيارات"):
                new_text = st.text_area("✏️ تعديل النص", value=note['content'], key=note_file)
                new_color = st.color_picker("🎨 تعديل اللون", value=note['color'], key=note_file + "_color")
                if st.button(f"حفظ التعديلات - {note_file}"):
                    save_json(path, {
                        "title": note['title'],
                        "content": new_text,
                        "color": new_color,
                        "time": str(datetime.now())
                    })
                    st.success("تم التعديل ✅")
                    st.rerun()
                if st.button(f"🗑️ حذف - {note_file}"):
                    delete_file(path)
                    st.warning("تم الحذف 🗑️")
                    st.rerun()

# ---------------- 📂 ملفات ----------------
if option == "📂 ملفات":
    st.header("📁 ملفاتك")
    uploaded_file = st.file_uploader("ارفع ملف", key="file")
    if uploaded_file:
        path = os.path.join(FILES_DIR, uploaded_file.name)
        with open(path, "wb") as f:
            f.write(uploaded_file.read())
        st.success("تم حفظ الملف ✅")
        st.rerun()

    for file in os.listdir(FILES_DIR):
        with st.expander(file):
            st.download_button("⬇️ تحميل", data=open(os.path.join(FILES_DIR, file), "rb"), file_name=file)
            if st.button(f"🗑️ حذف - {file}"):
                delete_file(os.path.join(FILES_DIR, file))
                st.warning("تم حذف الملف 🗑️")
                st.rerun()

# ---------------- 🖼️ صور ----------------
if option == "🖼️ صور":
    st.header("📷 صورك")
    image_file = st.file_uploader("ارفع صورة", type=["png", "jpg", "jpeg"], key="img")
    if image_file:
        path = os.path.join(IMAGES_DIR, image_file.name)
        with open(path, "wb") as f:
            f.write(image_file.read())
        st.success("✅ تم حفظ الصورة")
        st.rerun()

    for img in os.listdir(IMAGES_DIR):
        with st.expander(img):
            st.image(os.path.join(IMAGES_DIR, img))
            if st.button(f"🗑️ حذف - {img}"):
                delete_file(os.path.join(IMAGES_DIR, img))
                st.warning("تم الحذف")
                st.rerun()

# 1️⃣ Create virtual environment
python -m venv .venv

# 2️⃣ Allow activation scripts (only once if blocked)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3️⃣ Activate virtual environment
.venv\Scripts\Activate.ps1

# 4️⃣ Upgrade pip (good practice)
python -m pip install --upgrade pip

# 5️⃣ Install required dependencies
pip install streamlit pillow pandas matplotlib requests

# 6️⃣ Run your Streamlit app
streamlit run crypto_app.py

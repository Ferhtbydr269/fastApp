# EduFast — Eğitim Yönetim API'si

Öğrenci ve öğretmen rollerine sahip, **FastAPI** ile yazılmış bir REST API.
Kurs oluşturma, derse kayıt ve not yönetimini JWT kimlik doğrulama ve rol tabanlı yetkilendirmeyle sunar.

**Yığın:** FastAPI · SQLAlchemy · PostgreSQL (Supabase) · JWT · Pydantic · bcrypt

| Özellik | Açıklama |
|---|---|
| Kimlik doğrulama | JWT tabanlı giriş, bcrypt ile şifre saklama |
| Roller | Öğretmen kurs açar ve not verir; öğrenci kayıt olur ve notlarını görür |
| Doküman | Swagger UI otomatik üretilir (`/docs`) |

## Çalıştırma

```bash
cd edufast
python -m venv venv && venv\Scripts\activate   # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env                            # DATABASE_URL ve JWT_SECRET değerlerini doldur
uvicorn app.main:app --reload
```

Ayrıntılı dokümantasyon: [`edufast/README.md`](edufast/README.md)

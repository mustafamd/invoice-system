import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📊 نظام تحليل الفواتير")

# ✅ رفع عدة ملفات
uploaded_files = st.file_uploader(
    "📂 ارفع ملفات Excel",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []

    for file in uploaded_files:
        df_temp = pd.read_excel(file)

        # تنظيف + تصحيح أسماء الأعمدة
        df_temp.columns = df_temp.columns.str.strip()
        df_temp.columns = df_temp.columns.str.replace("مبلع", "مبلغ")

        dfs.append(df_temp)

    df = pd.concat(dfs, ignore_index=True)

    # الأعمدة المطلوبة
    required_columns = [
        "رقم فاتورة المحصل",
        "رقم الفاتورة",
        "المبلغ",
        "المكتب",
        "قناة الدفع",
        "مبلغ الايداع",
        "مبلغ سداد مباشر"
    ]

    # التحقق من الأعمدة
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        st.error(f"❌ الأعمدة الناقصة: {missing}")
        st.write("الأعمدة الموجودة:", df.columns.tolist())
        st.stop()

    df = df[required_columns]

    # تنظيف القيم
    df["المبلغ"] = df["المبلغ"].fillna(0)
    df["مبلغ الايداع"] = df["مبلغ الايداع"].fillna(0)
    df["مبلغ سداد مباشر"] = df["مبلغ سداد مباشر"].fillna(0)

    # 📋 عرض البيانات
    st.subheader("📋 البيانات")
    st.dataframe(df)

    # 🔍 البحث
    st.subheader("🔍 البحث")
    search_value = st.text_input("أدخل رقم الفاتورة أو رقم فاتورة المحصل")

    if search_value:
        result = df[
            (df["رقم الفاتورة"].astype(str) == search_value) |
            (df["رقم فاتورة المحصل"].astype(str) == search_value)
        ]
        st.dataframe(result)

    # 🔁 التكرار
    st.subheader("🔁 الفواتير المكررة")

    if st.button("عرض التكرار"):
        duplicates = df[
            df.duplicated(
                subset=["رقم الفاتورة", "المبلغ"],
                keep=False
            )
        ]
        st.dataframe(duplicates)

    # 💰 الإحصائيات
    st.subheader("💰 الإحصائيات")

    if st.button("عرض الإحصائيات"):
        paid = df[df["قناة الدفع"] == "سداد"]
        unpaid = df[df["قناة الدفع"] == "غير مدفوعه"]

        total_amount = df["المبلغ"].sum()
        total_deposit = df["مبلغ الايداع"].sum()
        total_direct = df["مبلغ سداد مباشر"].sum()

        st.write("📊 إجمالي المبلغ:", total_amount)
        st.write("🏦 إجمالي الإيداع:", total_deposit)
        st.write("💳 إجمالي سداد مباشر:", total_direct)
        st.write("✅ إجمالي سداد:", paid["المبلغ"].sum())
        st.write("❌ إجمالي غير مدفوع:", unpaid["المبلغ"].sum())

        # ✅ المعادلة
        result_value = (total_deposit + total_direct) - total_amount
        st.write("📉 ناتج المعادلة:", result_value)

        # إنشاء ملف Excel
        stats_df = pd.DataFrame({
            "البند": [
                "إجمالي المبلغ",
                "إجمالي الإيداع",
                "إجمالي السداد المباشر",
                "إجمالي سداد",
                "إجمالي غير مدفوع",
                "ناتج المعادلة"
            ],
            "القيمة": [
                total_amount,
                total_deposit,
                total_direct,
                paid["المبلغ"].sum(),
                unpaid["المبلغ"].sum(),
                result_value
            ]
        })

        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            stats_df.to_excel(writer, index=False, sheet_name="الإحصائيات")

        st.download_button(
            label="⬇️ تحميل الإحصائيات Excel",
            data=buffer.getvalue(),
            file_name="stats_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 🚨 البلاغات
    st.subheader("🚨 مقارنة البلاغات")

    complaints_file = st.file_uploader(
        "📂 ارفع ملف البلاغات",
        type=["xlsx"],
        key="complaints"
    )

    if complaints_file:
        complaints_df = pd.read_excel(complaints_file)
        complaints_df.columns = complaints_df.columns.str.strip()

        if "فاتورة بلاغات" not in complaints_df.columns:
            st.error("❌ لازم العمود يكون اسمه: فاتورة بلاغات")
        else:
            if st.button("عرض الفواتير التي عليها بلاغ"):
                result = df[
                    df["رقم الفاتورة"].astype(str).isin(
                        complaints_df["فاتورة بلاغات"].astype(str)
                    )
                ]

                st.dataframe(result)

                buffer2 = BytesIO()
                with pd.ExcelWriter(buffer2, engine="openpyxl") as writer:
                    result.to_excel(writer, index=False, sheet_name="البلاغات")

                st.download_button(
                    label="⬇️ تحميل نتائج البلاغات Excel",
                    data=buffer2.getvalue(),
                    file_name="complaints_results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

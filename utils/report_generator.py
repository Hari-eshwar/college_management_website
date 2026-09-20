import pandas as pd
import os
from datetime import datetime
import csv

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

HTML = None
def _get_weasyprint():
    global HTML
    if HTML is None:
        try:
            from weasyprint import HTML as _HTML
            HTML = _HTML
        except Exception:
            pass
    return HTML


class ReportGenerator:
    @staticmethod
    def generate_attendance_pdf(attendance_data, output_path, title='Smart Attendance Report'):
        wp = _get_weasyprint()
        if wp is None:
            return ReportGenerator._fallback_txt_pdf(attendance_data, output_path, title)
        rows_html = ''
        if attendance_data:
            headers = list(attendance_data[0].keys())
            header_cells = ''.join(f'<th>{h.replace("_", " ").title()}</th>' for h in headers)
            for row in attendance_data:
                cells = ''.join(f'<td>{str(row.get(h, ""))}</td>' for h in headers)
                rows_html += f'<tr>{cells}</tr>'
            body = f'''<table><thead><tr>{header_cells}</tr></thead><tbody>{rows_html}</tbody></table>'''
        else:
            body = '<p class="text-muted">No attendance data available.</p>'
        html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body {{ font-family: 'Helvetica', sans-serif; margin: 40px; color: #333; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 8px; }}
.sub {{ color: #7f8c8d; font-size: 14px; margin-bottom: 24px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
th {{ background: #3498db; color: white; padding: 10px 8px; text-align: left; }}
td {{ padding: 8px; border-bottom: 1px solid #ddd; }}
tr:nth-child(even) td {{ background: #f9f9f9; }}
.text-muted {{ color: #999; }}
</style></head><body>
<h1>{title}</h1>
<p class="sub">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
{body}
</body></html>'''
        os.makedirs(os.path.dirname(output_path), exist_ok=True) if os.path.dirname(output_path) else None
        wp(string=html).write_pdf(output_path)
        return output_path

    @staticmethod
    def _fallback_txt_pdf(attendance_data, output_path, title):
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(190, 15, txt=title, ln=True, align='C')
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(190, 8, txt=f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
        pdf.ln(10)
        if attendance_data:
            headers = list(attendance_data[0].keys())
            pdf.set_font('Arial', 'B', 10)
            col_w = 190 / len(headers)
            for h in headers:
                pdf.cell(col_w, 10, h.replace('_', ' ').title(), border=1)
            pdf.ln()
            pdf.set_font('Arial', '', 9)
            for row in attendance_data:
                for h in headers:
                    val = str(row.get(h, ''))
                    pdf.cell(col_w, 8, val[:20], border=1)
                pdf.ln()
        else:
            pdf.set_font('Arial', '', 12)
            pdf.cell(190, 10, txt='No attendance data available.', ln=True, align='C')
        pdf.output(output_path)
        return output_path

    @staticmethod
    def generate_attendance_excel(attendance_data, output_path):
        df = pd.DataFrame(attendance_data)
        if xlsxwriter:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            writer = pd.ExcelWriter(output_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Attendance', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Attendance']
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#3498db', 'font_color': 'white',
                                              'border': 1, 'text_wrap': True})
            for col_idx, col_name in enumerate(df.columns):
                worksheet.write(0, col_idx, col_name.replace('_', ' ').title(), header_fmt)
                worksheet.set_column(col_idx, col_idx, max(len(str(col_name)) + 2, 12))
            writer.close()
        else:
            df.to_excel(output_path, index=False)
        return output_path

    @staticmethod
    def generate_attendance_csv(attendance_data, output_path):
        if not attendance_data:
            with open(output_path, 'w', newline='') as f:
                f.write('')
            return output_path
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=attendance_data[0].keys())
            writer.writeheader()
            writer.writerows(attendance_data)
        return output_path

    @staticmethod
    def generate_comprehensive_report(attendance_data, output_path):
        return ReportGenerator._comprehensive_txt(attendance_data, output_path)

    @staticmethod
    def _comprehensive_txt(attendance_data, output_path):
        lines = ['=' * 50, 'SMART ATTENDANCE REPORT', '=' * 50,
                 f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                 f'Total Records: {len(attendance_data)}', '']
        if attendance_data:
            df = pd.DataFrame(attendance_data)
            if 'status' in df.columns:
                present = len(df[df['status'] == 'Present'])
                absent = len(df[df['status'] == 'Absent'])
                late = len(df[df['status'] == 'Late'])
                total = len(df)
                lines.extend(['--- ATTENDANCE SUMMARY ---',
                              f'Present: {present} ({present/total*100:.1f}%)' if total else 'Present: 0',
                              f'Absent: {absent} ({absent/total*100:.1f}%)' if total else 'Absent: 0',
                              f'Late: {late} ({late/total*100:.1f}%)' if total else 'Late: 0', ''])
        lines.extend(['=' * 50, 'End of Report'])
        if os.path.dirname(output_path):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(lines))
        return output_path
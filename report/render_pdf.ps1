# Convert the report .docx to PDF with Microsoft Word (used to check layout and to read page numbers).
param(
    [string]$Docx = "C:\skin_disease\report\Skin_Disease_Detection_Mini_Project_Report.docx",
    [string]$Pdf = "C:\skin_disease\report\Skin_Disease_Detection_Mini_Project_Report.pdf"
)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx, $false, $true)
    $doc.ExportAsFixedFormat($Pdf, 17)   # 17 = wdExportFormatPDF
    "pages: " + $doc.ComputeStatistics(2)
    $doc.Close($false)
} finally {
    $word.Quit()
}

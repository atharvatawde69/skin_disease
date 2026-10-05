# Export every slide of the presentation as a PNG (and the deck as PDF) using Microsoft PowerPoint, for visual checking.
param(
    [string]$Pptx = "C:\skin_disease\report\Skin_Disease_Detection_Presentation.pptx",
    [string]$OutDir = "C:\skin_disease\report\ppt_render"
)
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Force $OutDir | Out-Null
$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Open($Pptx, $true, $false, $false)
    $w = 1400
    $h = [int]($w * $pres.PageSetup.SlideHeight / $pres.PageSetup.SlideWidth)
    foreach ($s in $pres.Slides) { $s.Export("$OutDir\s{0:00}.png" -f $s.SlideIndex, "PNG", $w, $h) }
    $pres.SaveAs("$OutDir\deck.pdf", 32)   # 32 = ppSaveAsPDF
    "slides: " + $pres.Slides.Count + "  png: ${w}x${h}"
    $pres.Close()
} finally {
    $app.Quit()
}

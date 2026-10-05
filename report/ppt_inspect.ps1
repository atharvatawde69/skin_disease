# Convert the legacy .ppt template to .pptx with PowerPoint, export each slide as PNG, and dump slide/layout info.
param(
    [string]$Source = "C:\skin_disease\DL Lab Mini Project PPT Presentation_Template.ppt",
    [string]$OutDir = "C:\skin_disease\report\ppt_template"
)
New-Item -ItemType Directory -Force $OutDir | Out-Null
$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Open($Source, $true, $false, $false)   # read-only, untitled, no window
    "slides: " + $pres.Slides.Count + "   size: " + $pres.PageSetup.SlideWidth + " x " + $pres.PageSetup.SlideHeight
    foreach ($s in $pres.Slides) {
        "--- slide " + $s.SlideIndex + " layout=" + $s.CustomLayout.Name
        foreach ($sh in $s.Shapes) {
            $t = ""
            if ($sh.HasTextFrame) { $t = ($sh.TextFrame.TextRange.Text -replace "[\r\n\v]+", " / ") }
            "   [" + $sh.Name + "] type=" + $sh.Type + " pos=(" + [int]$sh.Left + "," + [int]$sh.Top + "," + [int]$sh.Width + "," + [int]$sh.Height + ") text=" + $t
        }
        $s.Export("$OutDir\slide_" + $s.SlideIndex + ".png", "PNG", 1280, 720)
    }
    "layouts:"
    foreach ($l in $pres.SlideMaster.CustomLayouts) { "   " + $l.Index + ": " + $l.Name }
    $pres.SaveCopyAs("$OutDir\template.pptx", 24)   # 24 = ppSaveAsOpenXMLPresentation
    $pres.Close()
} finally {
    $app.Quit()
}

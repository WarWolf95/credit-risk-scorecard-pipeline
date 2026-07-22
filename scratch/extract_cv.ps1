$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open("C:\Users\curil\Desktop\Maulik__CV_2026_Optimized.docx")
Write-Output $doc.Content.Text
$doc.Close()
$word.Quit()

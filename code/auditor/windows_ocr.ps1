param([Parameter(Mandatory=$true)][string]$ImagePath)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime] | Out-Null
$asyncMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
function AwaitResult($operation, $resultType) {
    $task = $asyncMethod.MakeGenericMethod($resultType).Invoke($null, @($operation))
    $task.Wait()
    return $task.Result
}
$file = AwaitResult ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$stream = AwaitResult ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = AwaitResult ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = AwaitResult ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$language = New-Object Windows.Globalization.Language 'en-US'
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
if ($null -eq $engine) { throw 'English Windows OCR language pack is unavailable.' }
$result = AwaitResult ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
$lines = @($result.Lines | ForEach-Object {
    $line = $_
    [pscustomobject]@{ text=$line.Text; words=@($line.Words | ForEach-Object { [pscustomobject]@{ text=$_.Text; x=$_.BoundingRect.X; y=$_.BoundingRect.Y; width=$_.BoundingRect.Width; height=$_.BoundingRect.Height } }) }
})
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[pscustomobject]@{ text=($result.Lines.Text -join "`n"); lines=$lines; engine='Windows.Media.Ocr'; width=$bitmap.PixelWidth; height=$bitmap.PixelHeight } | ConvertTo-Json -Depth 8 -Compress

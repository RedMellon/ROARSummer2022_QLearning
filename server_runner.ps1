# launch Carla
$carla = Start-Process -FilePath "C:\Users\gamev\Desktop\ROAR_Folders\Maps\MajorMap\WindowsNoEditor\CarlaUE4.exe" -PassThru
$carla = $carla | Get-Process

# infinite loop (Ctrl + C to stop script)
while ($True) {
    Start-Sleep -Seconds 5 # wait 5 seconds
    if ($carla.HasExited) { # if Carla process is closed
        # restart Carla
        $carla = Start-Process -FilePath "C:\Users\gamev\Desktop\ROAR_Folders\Maps\MajorMap\WindowsNoEditor\CarlaUE4.exe" -PassThru
        $carla = $carla | Get-Process
    }
}
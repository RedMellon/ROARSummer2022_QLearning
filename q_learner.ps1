# launch qlearn
# $qlearn = Start-Process -FilePath "C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py" -PassThru
# $qlearn = python C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py
# $qlearn = Start-Process python -FilePath "C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py" -PassThru
$qlearn = Start-Process "C:\Users\gamev\anaconda3\envs\ROAR_major\python.exe" -ArgumentList "C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py" -PassThru
$qlearn = $qlearn | Get-Process

# infinite loop (Ctrl + C to stop script)
while ($True) {
    Start-Sleep -Seconds 5 # wait 5 seconds
    if ($qlearn.HasExited) { # if qlearn process is closed
        # restart qlearn
        # $qlearn = Start-Process -FilePath "C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py" -PassThru
        # $qlearn = python C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py
        # $qlearn = Start-Process python -FilePath "C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py" -PassThru
        $qlearn = Start-Process "C:\Users\gamev\anaconda3\envs\ROAR_major\python.exe" -ArgumentList "C:\Users\gamev\Desktop\ROAR_Folders\Summer2022\ROAR_qlearning\q_learn.py" -PassThru
        $qlearn = $qlearn | Get-Process
    }
}
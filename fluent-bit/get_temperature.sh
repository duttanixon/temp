
#!/bin/bash

# Get GPU temperature
gpu_temp=$(vcgencmd measure_temp | grep -oE '[0-9]+\.[0-9]+')

# Get CPU temperature
cpu_temp=$(cat /sys/class/thermal/thermal_zone0/temp)
cpu_temp_c=$(echo "scale=1; $cpu_temp/1000" | bc)

# Output as JSON
echo "{\"gpu_temp\":$gpu_temp,\"cpu_temp\":$cpu_temp_c}"
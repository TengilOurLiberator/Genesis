execute positioned ~-0.5 ~-0.5 ~-0.5 as @e[type=#genesis:creature,dx=0,dy=0,dz=0,limit=1,sort=nearest] run tag @s add gen.looked
execute if entity @e[tag=gen.looked] run return run function genesis:look/found
execute unless block ~ ~ ~ #genesis:see_through run return 0
scoreboard players add #ray gen 1
execute if score #ray gen matches ..70 positioned ^ ^ ^0.5 run function genesis:look/step

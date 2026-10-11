execute as @a[tag=gen.lobby,tag=!gen.picked] at @s if block ~ ~-1 ~ minecraft:gold_block run function genesis:pick_adam
execute as @a[tag=gen.lobby,tag=!gen.picked] at @s if block ~ ~-1 ~ minecraft:diamond_block run function genesis:pick_eve
execute if score #count gen matches -1 if entity @a[tag=gen.lobby] unless entity @a[tag=gen.lobby,tag=!gen.picked] run scoreboard players set #count gen 80
execute if score #count gen matches 1.. run scoreboard players remove #count gen 1
execute if score #count gen matches 0 run function genesis:start

tag @a[tag=gen.viewer] add gen.human
tag @a remove gen.viewer
gamemode survival @a[tag=gen.human]
execute if entity @a[tag=gen.adam] run kill @e[tag=gen.m_adam]
execute if entity @a[tag=gen.eve] run kill @e[tag=gen.m_eve]
tag @e[tag=gen.figure] add gen.companion
execute as @e[tag=gen.companion] run data merge entity @s {Glowing:0b}
execute if entity @e[tag=gen.companion,tag=gen.m_eve] run scoreboard players set #companion gen 1
execute if entity @e[tag=gen.companion,tag=gen.m_adam] run scoreboard players set #companion gen 2
tp @a[tag=gen.human,tag=gen.adam] -222.50 69.00 -1.50
tp @a[tag=gen.human,tag=gen.eve] -222.50 69.00 2.50
effect clear @a[tag=gen.human] minecraft:resistance
execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base set 0
execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base set 0
kill @e[type=minecraft:marker,tag=gen.target]
summon minecraft:marker -222.50 69.00 2.50 {Tags:["gen.target"]}

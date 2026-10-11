tag @a[tag=gen.viewer] add gen.human
tag @a remove gen.viewer
gamemode survival @a[tag=gen.human]
tp @a[tag=gen.human,tag=gen.adam] -0.5 69.0 -1.5 90 0
tp @a[tag=gen.human,tag=gen.eve] -0.5 69.0 2.5 90 0
effect give @a[tag=gen.human] minecraft:blindness 2 0 true
effect clear @a[tag=gen.human] minecraft:resistance
execute as @a[tag=gen.human] run attribute @s minecraft:movement_speed base set 0
execute as @a[tag=gen.human] run attribute @s minecraft:jump_strength base set 0
execute unless entity @a[tag=gen.eve] run summon minecraft:mannequin -0.5 69.0 2.5 {Tags:["gen.companion","gen.eve"],CustomName:"Eve",Invulnerable:1b,PersistenceRequired:1b,profile:{texture:"genesis:entity/eve"}}
execute unless entity @a[tag=gen.eve] run scoreboard players set #companion gen 1
execute if entity @a[tag=gen.eve] unless entity @a[tag=gen.adam] run summon minecraft:mannequin -0.5 69.0 -1.5 {Tags:["gen.companion","gen.adam"],CustomName:"Adam",Invulnerable:1b,PersistenceRequired:1b,profile:{texture:"genesis:entity/adam"}}
execute if entity @a[tag=gen.eve] unless entity @a[tag=gen.adam] run scoreboard players set #companion gen 2
execute as @e[tag=gen.companion] at @s run rotate @s facing entity @p[tag=gen.human] eyes

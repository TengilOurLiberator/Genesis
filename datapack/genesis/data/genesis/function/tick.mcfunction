execute as @a[tag=!gen.seen] run function genesis:join
execute if score #phase gen matches 0 run function genesis:lobby
execute if score #phase gen matches 1 run function genesis:intro
execute store result score #b gen run time of genesis:day query time
execute if score #sunless gen matches 1 if score #b gen matches 24000.. run time of genesis:day set 0
execute if score #b gen matches 96000.. run time of genesis:day set 72000
execute if score #phase gen matches 2 as @e[tag=gen.companion] at @s run function genesis:companion/tick

tag @s add gen.seen
execute if score #phase gen matches 0 run function genesis:join_lobby
execute if score #phase gen matches 1 run function genesis:join_viewer
execute if score #phase gen matches 2 run function genesis:join_world

scoreboard players set #phase gen 0
scoreboard players set #t gen 0
scoreboard players set #sunless gen 1
scoreboard players set #count gen -1
scoreboard players set #companion gen 0
scoreboard players set #look gen 0
scoreboard players set #cmode gen 0
scoreboard players set #carrived gen 0
difficulty peaceful
gamerule minecraft:spawn_mobs false
gamerule minecraft:spawn_monsters false
gamerule minecraft:spawn_phantoms false
gamerule minecraft:spawn_wandering_traders false
gamerule minecraft:spawn_patrols false
gamerule minecraft:advance_weather false
gamerule minecraft:keep_inventory true
gamerule minecraft:mob_griefing false
gamerule minecraft:send_command_feedback false
gamerule minecraft:log_admin_commands false
gamerule minecraft:show_advancement_messages false
gamerule minecraft:locator_bar false
gamerule minecraft:player_movement_check false
gamerule minecraft:max_command_sequence_length 10000000
gamerule minecraft:max_block_modifications 10000000
gamerule minecraft:spectators_generate_chunks true
time of genesis:cut set 0
time of genesis:cut pause
time of genesis:day set 6000
time of genesis:day pause
forceload add -192 -136 -65 135
forceload add -64 -136 39 135
forceload add 40 -136 135 135
forceload add 992 992 1010 1008
setworldspawn 997 100 1000
schedule function genesis:setup2 60t
schedule function genesis:setup3 120t

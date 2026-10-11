fill 272 63 -14 272 63 -10 grass_block
fill 271 63 -16 271 63 -5 grass_block
fill 270 63 -17 270 63 -16 grass_block
fill 270 63 -6 270 63 -2 grass_block
fill 270 64 -15 270 64 -7 grass_block
place feature taiga_grass 230 69 157
place feature taiga_grass 231 67 158
place feature taiga_grass 230 66 160
place feature taiga_grass 232 65 161
place feature taiga_grass 229 65 162
place feature taiga_grass 229 65 163
place feature taiga_grass 228 67 163
place feature taiga_grass 229 64 164
place feature large_fern 250 65 80
setblock 252 64 81 fern
place feature seagrass_tall 175 43 279
place feature seagrass_short 172 43 294
place feature seagrass_short 166 43 295
place feature kelp 164 43 303
place feature seagrass_short 154 43 308
place feature seagrass_short 156 43 315
place feature kelp 144 43 326
place feature seagrass_short 136 43 330
place feature seagrass_short 145 43 331
place feature seagrass_short 132 43 335
place feature seagrass_tall 133 43 -339
place feature kelp 143 43 -332
place feature kelp 146 43 -324
place feature kelp 156 43 -314
place feature seagrass_tall 160 43 -310
place feature seagrass_short 162 43 -307
place feature kelp 157 43 -307
place feature seagrass_short 159 43 -306
place feature seagrass_short 163 43 -305
place feature kelp 165 43 -303
place feature kelp 165 43 -300
place feature kelp 166 43 -295
place feature seagrass_short 169 43 -287
place feature kelp 175 43 -281
place feature kelp 180 43 -279
place feature seagrass_mid 175 43 -279
place feature seagrass_mid 178 43 -278
place feature seagrass_mid 185 43 -274
place feature seagrass_mid 189 43 -263
place feature seagrass_mid 196 43 -250
place feature kelp 196 43 -244
place feature kelp 198 43 -242
place feature seagrass_mid 195 43 -242
place feature kelp 196 43 -239
place feature seagrass_mid 206 43 -232
place feature kelp 193 43 247
place feature kelp 198 43 251
place feature kelp 184 43 263
place feature kelp 184 43 267
place feature seagrass_mid 180 43 270
place feature seagrass_mid 184 43 272
place feature kelp 179 43 274
setblock -63 65 212 minecraft:air
place feature minecraft:mangrove -63 65 212
setblock -66 65 218 minecraft:air
place feature minecraft:tall_mangrove -66 65 218
setblock -66 64 210 minecraft:air
place feature minecraft:mangrove -66 64 210
setblock -67 64 214 minecraft:air
place feature minecraft:mangrove -67 64 214
execute as @a at @s run playsound minecraft:item.bone_meal.use ambient @s ~ ~ ~ 0.8 0.7 0.8
tp @e[type=minecraft:marker,tag=gen.cam,limit=1] -314.944 119.492 0.500

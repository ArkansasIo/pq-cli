/* Progress Quest browser RPG/MMORPG domain layer.
 * Mirrors the repository's Python domain concepts for static-browser play.
 * Network multiplayer and authoritative persistence require a server adapter.
 */
(function (root) {
  "use strict";
  const ATTRIBUTES = ["strength","dexterity","constitution","intelligence","wisdom","vitality","spirit","luck","willpower","charisma"];
  const ATTRIBUTE_LABELS = {strength:"Strength",dexterity:"Dexterity",constitution:"Constitution",intelligence:"Intelligence",wisdom:"Wisdom",vitality:"Vitality",spirit:"Spirit",luck:"Luck",willpower:"Willpower",charisma:"Charisma"};
  const RACES = {
    Human:{strength:1,dexterity:1,constitution:1,intelligence:1,wisdom:1,vitality:1,spirit:1,luck:2,willpower:1,charisma:2},
    Elf:{strength:0,dexterity:3,constitution:0,intelligence:2,wisdom:2,vitality:0,spirit:2,luck:1,willpower:1,charisma:1},
    Dwarf:{strength:2,dexterity:0,constitution:3,intelligence:0,wisdom:1,vitality:3,spirit:1,luck:0,willpower:2,charisma:0},
    Halfling:{strength:0,dexterity:3,constitution:1,intelligence:1,wisdom:1,vitality:1,spirit:0,luck:4,willpower:1,charisma:2},
    Orc:{strength:4,dexterity:1,constitution:2,intelligence:0,wisdom:0,vitality:3,spirit:0,luck:1,willpower:2,charisma:0}
  };
  const CLASSES = {
    Fighter:{primary:"strength",resource:"rage",growth:{strength:2,constitution:1}},
    Wizard:{primary:"intelligence",resource:"mp",growth:{intelligence:2,spirit:1}},
    Rogue:{primary:"dexterity",resource:"stamina",growth:{dexterity:2,luck:1}},
    Cleric:{primary:"wisdom",resource:"mp",growth:{wisdom:2,spirit:1}},
    Ranger:{primary:"dexterity",resource:"stamina",growth:{dexterity:1,wisdom:1}}
  };
  const SUBCLASSES = {
    Fighter:["Vanguard","Berserker","Sentinel"],Wizard:["Arcanist","Elementalist","Sage"],
    Rogue:["Assassin","Shadow","Trickster"],Cleric:["Templar","Oracle","Warden"],
    Ranger:["Beastmaster","Pathfinder","Sharpshooter"]
  };
  const EQUIPMENT_SLOTS = ["weapon","head","chest","hands","legs","feet","amulet","ring","offhand"];
  const RARITIES = ["common","uncommon","rare","epic","legendary","mythic"];
  const DAMAGE_TYPES = ["physical","fire","ice","lightning","poison","arcane","holy","shadow"];
  const SKILLS = [
    {id:"strike",name:"Power Strike",type:"active",cost:15,scaling:"strength",description:"A forceful strike that increases attack damage."},
    {id:"firebolt",name:"Firebolt",type:"active",cost:12,scaling:"intelligence",description:"Arcane fire damage against a single enemy."},
    {id:"mend",name:"Mend",type:"active",cost:18,scaling:"wisdom",description:"Restore a portion of missing health."},
    {id:"guard",name:"Iron Guard",type:"passive",cost:0,scaling:"constitution",description:"Reduce incoming damage."},
    {id:"fortune",name:"Fortune",type:"passive",cost:0,scaling:"luck",description:"Improve critical chance and loot."}
  ];
  const TALENT_TREES = {
    assault:[{id:"assault_1",name:"Weapon Training",max:5,attribute:"strength",perRank:2},{id:"assault_2",name:"Critical Focus",max:5,attribute:"dexterity",perRank:1}],
    survival:[{id:"survival_1",name:"Vital Reserves",max:5,attribute:"vitality",perRank:3},{id:"survival_2",name:"Iron Skin",max:5,attribute:"constitution",perRank:2}],
    mystic:[{id:"mystic_1",name:"Arcane Study",max:5,attribute:"intelligence",perRank:2},{id:"mystic_2",name:"Spirit Well",max:5,attribute:"spirit",perRank:3}]
  };
  const QUESTS = [
    {id:"first_steps",name:"First Steps",objective:{type:"kill",target:5},rewards:{xp:50,gold:25}},
    {id:"explorer",name:"Explorer",objective:{type:"zone",target:2},rewards:{xp:100,gold:50}},
    {id:"crafting_apprentice",name:"Crafting Apprentice",objective:{type:"craft",target:1},rewards:{xp:75,gold:35}},
    {id:"slayer",name:"Monster Slayer",objective:{type:"kill",target:25},rewards:{xp:250,gold:150}}
  ];
  const RECIPES = [
    {id:"iron_blade",name:"Iron Blade",profession:"smithing",level:1,ingredients:{iron:3,wood:1},result:{type:"equipment",slot:"weapon",power:5}},
    {id:"reinforced_armor",name:"Reinforced Armor",profession:"smithing",level:2,ingredients:{iron:5,hide:2},result:{type:"equipment",slot:"chest",power:8}},
    {id:"healing_tonic",name:"Healing Tonic",profession:"alchemy",level:1,ingredients:{herb:2,water:1},result:{type:"consumable",effect:"heal",power:35}},
    {id:"mana_tonic",name:"Mana Tonic",profession:"alchemy",level:2,ingredients:{herb:2,crystal:1,water:1},result:{type:"consumable",effect:"mana",power:30}}
  ];
  const BIOMES = ["grassland","forest","ruins","cavern","highlands","volcanic","tundra","swamp","desert","celestial"];
  const ZONES = [
    {id:"greenway",name:"The Greenway",biome:"grassland",minLevel:1,requiredKills:0},
    {id:"mosswood",name:"Mosswood Forest",biome:"forest",minLevel:3,requiredKills:4},
    {id:"ruins",name:"Forgotten Ruins",biome:"ruins",minLevel:5,requiredKills:10},
    {id:"caverns",name:"Whispering Caverns",biome:"cavern",minLevel:8,requiredKills:18},
    {id:"highlands",name:"Ashen Highlands",biome:"highlands",minLevel:12,requiredKills:30},
    {id:"dragon_reach",name:"Dragon's Reach",biome:"volcanic",minLevel:18,requiredKills:45},
    {id:"frostfall",name:"Frostfall Expanse",biome:"tundra",minLevel:24,requiredKills:65},
    {id:"sunken_mire",name:"Sunken Mire",biome:"swamp",minLevel:30,requiredKills:90}
  ];
  const DUNGEONS = [
    {id:"root_cellar",name:"Root Cellar",minLevel:3,boss:"Mossback Brute",partySize:1,lootTier:1},
    {id:"sunken_archive",name:"Sunken Archive",minLevel:8,boss:"The Drowned Scribe",partySize:1,lootTier:2},
    {id:"ember_keep",name:"Ember Keep",minLevel:15,boss:"Ashen Warden",partySize:1,lootTier:3},
    {id:"dragon_vault",name:"Dragon Vault",minLevel:25,boss:"Vault Dragon",partySize:1,lootTier:4}
  ];
  const PROFESSIONS = ["smithing","alchemy","cooking","enchanting","gathering"];
  const FACTIONS = ["Wayfarers' Guild","Cinder Court","Verdant Circle","Ancient Watch"];
  const ACHIEVEMENTS = [
    {id:"first_blood",name:"First Blood",condition:"kills >= 1",points:5},
    {id:"veteran",name:"Veteran",condition:"level >= 10",points:20},
    {id:"collector",name:"Collector",condition:"items >= 10",points:15},
    {id:"artisan",name:"Artisan",condition:"crafted >= 5",points:15},
    {id:"world_walker",name:"World Walker",condition:"zones >= 5",points:25}
  ];
  const EVENTS = [
    {id:"wolf_moon",name:"Wolf Moon",description:"Wild creatures are more common.",bonus:"loot"},
    {id:"merchant_fair",name:"Merchant Fair",description:"Vendors offer better sale prices.",bonus:"economy"},
    {id:"arcane_surges",name:"Arcane Surges",description:"Magic finds extra crystals.",bonus:"crafting"}
  ];
  const MOUNTS = [
    {id:"trail_horse",name:"Trail Horse",speed:0.05,unlockKills:10},
    {id:"moss_stag",name:"Moss Stag",speed:0.1,unlockKills:30},
    {id:"ember_drake",name:"Ember Drake",speed:0.15,unlockKills:60}
  ];
  const defaults = () => ({
    schemaVersion:1,identity:{id:"hero-"+Math.random().toString(36).slice(2),createdAt:new Date().toISOString()},
    level:1,xp:0,xpToNext:100,attributes:Object.fromEntries(ATTRIBUTES.map(k=>[k,10])),
    resources:{hp:100,mp:50,stamina:100,rage:0},classId:"Fighter",subclassId:"Vanguard",raceId:"Human",
    equipment:Object.fromEntries(EQUIPMENT_SLOTS.map(k=>[k,null])),inventory:[],currencies:{gold:0,shards:0},
    skills:Object.fromEntries(SKILLS.map(x=>[x.id,{rank:0,unlocked:x.id==="strike",cooldown:0}])),
    talents:{points:0,ranks:{}},professions:Object.fromEntries(PROFESSIONS.map(k=>[k,{level:1,xp:0}])),
    materials:{iron:0,wood:0,hide:0,herb:0,water:0,crystal:0,meat:0},
    quests:{active:["first_steps"],progress:{},completed:[]},achievements:[],reputation:Object.fromEntries(FACTIONS.map(k=>[k,0])),
    world:{zoneId:"greenway",unlockedZones:["greenway"],kills:0,discoveredDungeons:[],completedDungeons:[]},
    party:{members:[],formation:"balanced"},guild:{name:"",rank:"none",members:[]},friends:[],blocked:[],
    pvp:{rating:1000,wins:0,losses:0,season:"season-1"},mounts:{owned:[],active:null},
    market:{listings:[],orders:[]},mail:[],settings:{autoBattle:true,battleSpeed:3000,priority:"balanced"},statistics:{kills:0,deaths:0,crafted:0,zonesVisited:1}
  });
  function derive(attributes, bonuses) {
    const a={...Object.fromEntries(ATTRIBUTES.map(k=>[k,10])),...(attributes||{})}, b=bonuses||{};
    return {
      maxHp:Math.max(1,a.vitality*15+a.constitution*10+(b.maxHp||0)),
      maxMp:Math.max(0,a.spirit*5+a.intelligence*10+(b.maxMp||0)),
      attack:Math.max(1,a.strength*2+a.dexterity+(b.attack||0)),
      spellPower:Math.max(0,a.intelligence*2+a.wisdom+(b.spellPower||0)),
      armor:Math.max(0,a.constitution*2+a.vitality+(b.armor||0)),
      magicResist:Math.max(0,a.wisdom+a.spirit+(b.magicResist||0)),
      critChance:Math.min(.75,.02+a.dexterity/500+(b.critChance||0)),
      critMultiplier:1.5+(b.critMultiplier||0),
      dodgeChance:Math.min(.5,.01+a.dexterity/400+(b.dodgeChance||0)),
      blockChance:Math.min(.75,(b.blockChance||0)),
      haste:Math.max(0,b.haste||0),moveSpeed:1+(b.moveSpeed||0),
      lifeSteal:Math.max(0,b.lifeSteal||0),threat:Math.max(.1,b.threat||1)
    };
  }
  function equipmentBonuses(state) {
    const result={};
    for(const item of Object.values(state.equipment||{})) if(item&&item.stats)
      for(const [k,v] of Object.entries(item.stats)) result[k]=(result[k]||0)+v;
    return result;
  }
  function rollDamage(attacker, defender, type) {
    const physical=type==="physical";
    const base=physical?attacker.attack:attacker.spellPower;
    const mitigation=physical?defender.armor:defender.magicResist;
    const crit=Math.random()<attacker.critChance;
    const raw=Math.max(1,base*(crit?attacker.critMultiplier:1));
    const dodge=Math.random()<defender.dodgeChance;
    const block=!dodge&&Math.random()<defender.blockChance;
    return {damage:dodge?0:Math.max(1,Math.round(raw*(100/(100+Math.max(0,mitigation)))*(block?.5:1))),critical:crit,dodged:dodge,blocked:block,type:type||"physical"};
  }
  function makeItem(id,name,slot,rarity,power,stats) {
    return {id,name,slot,rarity:RARITIES.includes(rarity)?rarity:"common",itemLevel:1+Math.floor(power),power,stats:stats||{},stackable:false,quantity:1,bound:false};
  }
  function validateSave(state) {
    if(!state||typeof state!=="object"||!state.attributes||!state.resources||!state.equipment) throw new Error("Invalid RPG save structure");
    for(const k of ATTRIBUTES) if(!Number.isFinite(Number(state.attributes[k]))) throw new Error("Invalid attribute: "+k);
    return {...defaults(),...state,attributes:{...defaults().attributes,...state.attributes},resources:{...defaults().resources,...state.resources}};
  }
  function grantXp(state, amount) {
    state.xp+=Math.max(0,Math.floor(amount));let levels=0;
    while(state.xp>=Math.floor(100*Math.pow(state.level,1.55))){state.xp-=Math.floor(100*Math.pow(state.level,1.55));state.level++;state.talents.points++;levels++;const growth=CLASSES[state.classId]?.growth||{strength:1};for(const [k,v] of Object.entries(growth))state.attributes[k]+=v;}
    return levels;
  }
  function unlockZones(state){for(const z of ZONES)if(state.world.kills>=z.requiredKills&&!state.world.unlockedZones.includes(z.id))state.world.unlockedZones.push(z.id);return state.world.unlockedZones;}
  function makeLoot(state){const rarityRoll=Math.random(),rarity=rarityRoll>.98?"legendary":rarityRoll>.9?"epic":rarityRoll>.7?"rare":rarityRoll>.4?"uncommon":"common";const slot=EQUIPMENT_SLOTS[Math.floor(Math.random()*EQUIPMENT_SLOTS.length)];const power=Math.max(1,Math.floor(state.level*(1+RARITIES.indexOf(rarity)*.25)));return makeItem("loot-"+Date.now().toString(36)+Math.random().toString(36).slice(2,6),rarity+" "+slot,slot,rarity,power,{attack:slot==="weapon"?power:0,armor:slot==="chest"||slot==="head"?power:0,maxHp:slot==="chest"?power*2:0});}
  function craft(state, recipeId) {
    const r=RECIPES.find(x=>x.id===recipeId);if(!r)throw new Error("Unknown recipe");
    for(const [k,v] of Object.entries(r.ingredients))if((state.materials[k]||0)<v)throw new Error("Not enough "+k);
    for(const [k,v] of Object.entries(r.ingredients))state.materials[k]-=v;
    state.professions[r.profession].xp+=10;state.statistics.crafted++;
    const result=r.result.type==="equipment"?makeItem("crafted-"+Date.now().toString(36),r.name,r.result.slot,"uncommon",r.result.power,{attack:r.result.slot==="weapon"?r.result.power:0,armor:r.result.slot==="chest"?r.result.power:0}):{id:"consumable-"+Date.now().toString(36),name:r.name,type:"consumable",effect:r.result.effect,power:r.result.power,quantity:1,stackable:true};
    state.inventory.push(result);return result;
  }
  const api={
    schemaVersion:1,ATTRIBUTES,ATTRIBUTE_LABELS,RACES,CLASSES,SUBCLASSES,EQUIPMENT_SLOTS,RARITIES,DAMAGE_TYPES,SKILLS,TALENT_TREES,
    QUESTS,RECIPES,BIOMES,ZONES,DUNGEONS,PROFESSIONS,FACTIONS,ACHIEVEMENTS,EVENTS,MOUNTS,defaults,derive,equipmentBonuses,rollDamage,makeItem,validateSave,grantXp,unlockZones,makeLoot,craft
  };
  root.PQMMO=api;
})(window);
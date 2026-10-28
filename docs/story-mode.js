/* Original story-mode campaign content for Progress Quest browser edition.
 * Uses the open 5e-compatible rules framework as inspiration, not copied adventure-book text.
 * Story, names, dialogue, locations, and quest text here are original.
 */
(function(root) {
 "use strict";
 const CAMPAIGN = {
  id:"the-shattered-accord", title:"The Shattered Accord", version:1,
  premise:"A network of ancient waystones is failing. Each region remembers a different piece of the Accord that once kept the wild magic in balance.",
  chapters:[
   {id:"ch1",title:"A Bell Beneath the Greenway",recommendedLevel:1,zone:"greenway",
    opening:"At dusk, the old road bell rings from beneath the earth. The village keeper asks you to find the missing waystone seal before the road disappears into mist.",
    objectives:[{id:"slimes",type:"kill",target:3,label:"Defeat 3 creatures along the old road"},{id:"gather",type:"collect",item:"crystal",target:1,label:"Recover 1 waystone crystal"}],
    choices:[{id:"mercy",label:"Protect the frightened road-sprite",effects:{reputation:{"Verdant Circle":5},rewardGold:10},result:"The sprite marks a safe path through the woods."},{id:"pragmatic",label:"Take the seal and move quickly",effects:{rewardGold:20},result:"You gain a little coin, but the forest remains wary."}],
    completion:"The seal warms in your hand. A thin blue line appears on the map, pointing toward Mosswood."
   },
   {id:"ch2",title:"The Memory of Mosswood",recommendedLevel:3,zone:"mosswood",
    opening:"In Mosswood, roots have grown around a watchtower whose stones hum at night. The tower's archivist will trade its history for proof that the nearby paths are safe.",
    objectives:[{id:"forest",type:"kill",target:5,label:"Clear 5 threats from the forest paths"},{id:"herbs",type:"collect",item:"herb",target:2,label:"Gather 2 restorative herbs"}],
    choices:[{id:"restore",label:"Restore the tower's ward",effects:{reputation:{"Ancient Watch":10},rewardShard:1},result:"The tower lights up and reveals an old route."},{id:"salvage",label:"Salvage its useful parts",effects:{rewardGold:35},result:"You earn supplies, though the tower stays dark."}],
    completion:"The archivist shares a fragment: the Accord was built by many peoples, not one crown."
   },
   {id:"ch3",title:"The Archive That Sank",recommendedLevel:8,zone:"caverns",
    opening:"An underground archive has slipped below a flooded cavern. Its guardian tests visitors with echoes of choices made earlier in the journey.",
    objectives:[{id:"cavern",type:"kill",target:8,label:"Defeat 8 cavern enemies"},{id:"craft",type:"craft",target:1,label:"Craft one item for the expedition"}],
    choices:[{id:"share",label:"Share the recovered records",effects:{reputation:{"Wayfarers' Guild":10},rewardShard:2},result:"The records become a common resource for future travelers."},{id:"keep",label:"Keep the records for yourself",effects:{rewardGold:60},result:"The records are valuable, but fewer allies learn from them."}],
    completion:"The records identify a final beacon beyond the Ashen Highlands."
   },
   {id:"ch4",title:"The Ashen Beacon",recommendedLevel:12,zone:"highlands",
    opening:"At the highland beacon, a storm of unbound magic tears across the ridge. The last seal can be repaired only by combining your gathered materials and the trust you earned.",
    objectives:[{id:"highland",type:"kill",target:12,label:"Defeat 12 highland threats"},{id:"beacon",type:"collect",item:"crystal",target:3,label:"Gather 3 crystals for the beacon"}],
    choices:[{id:"bind",label:"Bind the beacon with a shared oath",effects:{reputation:{"Ancient Watch":15,"Verdant Circle":10},rewardShard:3},result:"The beacon steadies, and its light reaches every restored waystone."},{id:"channel",label:"Channel the beacon into your own gear",effects:{rewardGold:100},result:"Your equipment hums with power, but the Accord remains fragile."}],
    completion:"The roads reconnect. New expeditions begin, and the world opens beyond the first map."
   }
  ]
 };
 const CAMPAIGN_RULES = {
  checks:["ability_check","saving_throw","attack_roll","skill_check"],
  abilityModifier: score => Math.floor((score-10)/2),
  proficiencyBonus: level => level<5?2:level<9?3:level<13?4:level<17?5:6,
  d20:()=>1+Math.floor(Math.random()*20),
  check:(score,proficiency,dc)=>{const roll=1+Math.floor(Math.random()*20);return {roll,total:roll+Math.floor((score-10)/2)+(proficiency||0),dc,success:roll===20|| (roll!==1&&roll+Math.floor((score-10)/2)+(proficiency||0)>=dc),critical:roll===20,fumble:roll===1};}
 };
 function newProgress(){return {campaignId:CAMPAIGN.id,chapterIndex:0,objectives:{},choices:{},completedChapters:[],flags:{},startedAt:new Date().toISOString()};}
 function current(progress){return CAMPAIGN.chapters[progress.chapterIndex]||null;}
 function objectiveProgress(progress,chapterId,objectiveId){return (progress.objectives[chapterId]&&progress.objectives[chapterId][objectiveId])||0;}
 function record(progress,chapterId,objectiveId,amount){if(!progress.objectives[chapterId])progress.objectives[chapterId]={};progress.objectives[chapterId][objectiveId]=Math.max(0,objectiveProgress(progress,chapterId,objectiveId)+(amount||1));}
 function ready(progress,chapter){return chapter.objectives.every(o=>objectiveProgress(progress,chapter.id,o.id)>=o.target);}
 function choose(progress,chapter,choiceId){const c=chapter.choices.find(x=>x.id===choiceId);if(!c)throw new Error("Unknown story choice");progress.choices[chapter.id]=choiceId;progress.flags[chapter.id+"_"+choiceId]=true;return c;}
 function complete(progress,chapter){if(!ready(progress,chapter))throw new Error("Story objectives are not complete");if(!progress.completedChapters.includes(chapter.id))progress.completedChapters.push(chapter.id);if(progress.chapterIndex<CAMPAIGN.chapters.length-1)progress.chapterIndex++;else progress.chapterIndex=CAMPAIGN.chapters.length;return chapter.completion;}
 root.PQStory={CAMPAIGN,CAMPAIGN_RULES,newProgress,current,objectiveProgress,record,ready,choose,complete};
})(window);
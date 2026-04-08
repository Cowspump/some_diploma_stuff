"""
Auto-seed: populates the database with test data if it's empty.
Called from main.py on startup.
"""
import logging
import random
import models
import auth
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

THERAPIST = {"full_name": "Dr. Anna Petrova", "mail": "anna@test.com", "password": "password123", "role": "therapist"}
WORKERS = [
    {"full_name": "Иван Сидоров", "mail": "ivan@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Maria Chen", "mail": "maria@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Алексей Козлов", "mail": "alexey@test.com", "password": "password123", "role": "worker"},
    {"full_name": "Li Wei", "mail": "liwei@test.com", "password": "password123", "role": "worker"},
]

TESTS = [
    {
        "title": "职业倦怠评估量表",
        "description": "请根据你最近一段时间的工作或学习状态，评估职业倦怠程度",
        "questions": [
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（情绪耗竭）：", "options": [
                {"text": "我长期感到情绪被完全耗尽，几乎每天如此", "points": 0}, {"text": "我经常感到情绪疲惫", "points": 1},
                {"text": "我有时会感到疲劳", "points": 2}, {"text": "我精力充沛", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作疲劳）：", "options": [
                {"text": "每天工作都会让我感到极度疲惫", "points": 0}, {"text": "工作后经常感到很累", "points": 1},
                {"text": "有时感到疲劳", "points": 2}, {"text": "工作后状态良好", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作压力）：", "options": [
                {"text": "我一想到工作就感到强烈压力甚至抗拒", "points": 0}, {"text": "我经常对工作感到明显压力", "points": 1},
                {"text": "我有一定压力，但可以应对", "points": 2}, {"text": "我可以轻松面对工作", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作负担）：", "options": [
                {"text": "我觉得自己已经无法承受当前的工作负担", "points": 0}, {"text": "我感觉工作负担较重", "points": 1},
                {"text": "工作负担尚可接受", "points": 2}, {"text": "工作负担正常", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（情绪恢复）：", "options": [
                {"text": "我感到情绪被完全掏空，难以恢复", "points": 0}, {"text": "我经常感到情绪低落", "points": 1},
                {"text": "偶尔有这种感觉", "points": 2}, {"text": "情绪基本稳定", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（精力状况）：", "options": [
                {"text": "我觉得自己在工作中已经精疲力尽", "points": 0}, {"text": "经常感到精力不足", "points": 1},
                {"text": "偶尔疲惫", "points": 2}, {"text": "精力充足", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作兴趣）：", "options": [
                {"text": "我对工作感到极度厌倦甚至抗拒", "points": 0}, {"text": "我对工作有明显厌倦感", "points": 1},
                {"text": "偶尔会感到厌倦", "points": 2}, {"text": "我对工作仍然保持兴趣", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（开始工作）：", "options": [
                {"text": "我觉得每天开始工作都非常困难", "points": 0}, {"text": "我经常拖延或不想开始工作", "points": 1},
                {"text": "有时会拖延", "points": 2}, {"text": "我可以正常开始工作", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作情绪）：", "options": [
                {"text": "工作让我感到情绪崩溃或难以承受", "points": 0}, {"text": "工作让我压力很大", "points": 1},
                {"text": "有一定压力", "points": 2}, {"text": "工作压力在可控范围内", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（对他人态度）：", "options": [
                {"text": "我对他人变得冷漠甚至无感", "points": 0}, {"text": "我有时对他人不耐烦", "points": 1},
                {"text": "偶尔表现出冷淡", "points": 2}, {"text": "我对他人保持正常态度", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（关心他人）：", "options": [
                {"text": "我对他人的问题完全不关心", "points": 0}, {"text": "我不太愿意关心他人", "points": 1},
                {"text": "有时会疏远他人", "points": 2}, {"text": "我愿意理解和关心他人", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（尊重他人）：", "options": [
                {"text": "我把他人当作任务对象而不是人", "points": 0}, {"text": "有时会这样看待他人", "points": 1},
                {"text": "偶尔出现这种情况", "points": 2}, {"text": "我始终尊重他人", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（耐心程度）：", "options": [
                {"text": "我对他人明显缺乏耐心", "points": 0}, {"text": "我容易烦躁或不耐烦", "points": 1},
                {"text": "偶尔会这样", "points": 2}, {"text": "我通常比较有耐心", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（沟通意愿）：", "options": [
                {"text": "我不愿意与他人沟通或交流", "points": 0}, {"text": "我减少了与他人的交流", "points": 1},
                {"text": "偶尔回避沟通", "points": 2}, {"text": "我愿意主动沟通", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（负面情绪）：", "options": [
                {"text": "我对工作相关的人产生明显负面情绪", "points": 0}, {"text": "经常会有负面情绪", "points": 1},
                {"text": "偶尔出现", "points": 2}, {"text": "情绪基本稳定", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（社交疲劳）：", "options": [
                {"text": "我觉得与人相处让我非常疲惫", "points": 0}, {"text": "我经常感到社交疲劳", "points": 1},
                {"text": "偶尔会有这种感觉", "points": 2}, {"text": "我可以良好地与他人相处", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（成就感）：", "options": [
                {"text": "我觉得自己在工作中毫无成就", "points": 0}, {"text": "我的成就感较低", "points": 1},
                {"text": "我有一定成就感", "points": 2}, {"text": "我有较强的成就感", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（自信程度）：", "options": [
                {"text": "我觉得自己能力不足，难以胜任工作", "points": 0}, {"text": "我对自己不太有信心", "points": 1},
                {"text": "我基本可以胜任", "points": 2}, {"text": "我对自己的能力有信心", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作价值）：", "options": [
                {"text": "我觉得自己的工作没有意义或价值", "points": 0}, {"text": "我觉得价值感较低", "points": 1},
                {"text": "我觉得工作有一定价值", "points": 2}, {"text": "我认为工作具有重要意义", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（帮助他人）：", "options": [
                {"text": "我觉得自己无法有效帮助他人", "points": 0}, {"text": "我的帮助能力有限", "points": 1},
                {"text": "我可以提供一定帮助", "points": 2}, {"text": "我能够有效帮助他人", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（工作满意度）：", "options": [
                {"text": "我对自己的工作表现非常不满意", "points": 0}, {"text": "我对表现不太满意", "points": 1},
                {"text": "我基本满意", "points": 2}, {"text": "我对表现很满意", "points": 3}]},
            {"text": "请根据你最近一段时间的工作或学习状态，选择最符合你情况的一项（个人成长）：", "options": [
                {"text": "我觉得自己在职业或学习中没有成长", "points": 0}, {"text": "我的成长较为有限", "points": 1},
                {"text": "我有一定成长", "points": 2}, {"text": "我持续在成长和进步", "points": 3}]},
        ],
    },
    {
        "title": "焦虑状态评估量表",
        "description": "评估您当前的焦虑水平",
        "questions": [
            {"text": "紧张感", "options": [
                {"text": "我几乎一直处于高度紧张状态", "points": 0}, {"text": "我经常感到紧张", "points": 1},
                {"text": "我偶尔感到紧张", "points": 2}, {"text": "我很少感到紧张", "points": 3}]},
            {"text": "无法放松", "options": [
                {"text": "我完全无法放松", "points": 0}, {"text": "我很难放松", "points": 1},
                {"text": "我有时可以放松", "points": 2}, {"text": "我可以轻松放松", "points": 3}]},
            {"text": "对未知的担忧", "options": [
                {"text": "我对未来或未知感到强烈恐惧", "points": 0}, {"text": "我经常担心未来", "points": 1},
                {"text": "我有一些担忧", "points": 2}, {"text": "我很少担忧", "points": 3}]},
            {"text": "心跳加快", "options": [
                {"text": "我经常感到心跳异常快或强烈", "points": 0}, {"text": "我有时会心跳加快", "points": 1},
                {"text": "偶尔出现", "points": 2}, {"text": "几乎没有", "points": 3}]},
            {"text": "呼吸困难", "options": [
                {"text": "我经常感到呼吸困难", "points": 0}, {"text": "有时感到呼吸不顺", "points": 1},
                {"text": "偶尔出现", "points": 2}, {"text": "没有这种情况", "points": 3}]},
            {"text": "出汗", "options": [
                {"text": "即使不热也经常出汗", "points": 0}, {"text": "有时会异常出汗", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "正常", "points": 3}]},
            {"text": "手抖或身体发抖", "options": [
                {"text": "经常明显发抖", "points": 0}, {"text": "有时发抖", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "没有", "points": 3}]},
            {"text": "害怕失控", "options": [
                {"text": "我经常觉得自己会失去控制", "points": 0}, {"text": "我有时担心失控", "points": 1},
                {"text": "偶尔有这种感觉", "points": 2}, {"text": "我感觉自己可以控制情绪", "points": 3}]},
            {"text": "灾难化思维", "options": [
                {"text": "我经常预想最坏结果", "points": 0}, {"text": "我经常往坏处想", "points": 1},
                {"text": "有时会这样", "points": 2}, {"text": "我通常能理性思考", "points": 3}]},
            {"text": "坐立不安", "options": [
                {"text": "我几乎无法静下来", "points": 0}, {"text": "我经常感到不安", "points": 1},
                {"text": "偶尔不安", "points": 2}, {"text": "我可以保持平静", "points": 3}]},
            {"text": "易受惊吓", "options": [
                {"text": "我非常容易受到惊吓", "points": 0}, {"text": "我比以前更容易受惊", "points": 1},
                {"text": "有一点变化", "points": 2}, {"text": "正常", "points": 3}]},
            {"text": "注意力困难", "options": [
                {"text": "我几乎无法集中注意力", "points": 0}, {"text": "很难集中", "points": 1},
                {"text": "偶尔困难", "points": 2}, {"text": "正常", "points": 3}]},
            {"text": "过度警觉", "options": [
                {"text": "我一直处于警觉状态", "points": 0}, {"text": "经常紧绷", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "放松正常", "points": 3}]},
            {"text": "对身体不适的担忧", "options": [
                {"text": "我非常担心身体症状", "points": 0}, {"text": "经常担心", "points": 1},
                {"text": "偶尔担心", "points": 2}, {"text": "不担心", "points": 3}]},
            {"text": "失眠或难以入睡", "options": [
                {"text": "严重影响睡眠", "points": 0}, {"text": "经常难入睡", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "睡眠正常", "points": 3}]},
            {"text": "肌肉紧张", "options": [
                {"text": "持续紧张或疼痛", "points": 0}, {"text": "经常紧绷", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "放松", "points": 3}]},
            {"text": "回避行为", "options": [
                {"text": "我避免很多活动或场景", "points": 0}, {"text": "我经常回避", "points": 1},
                {"text": "偶尔回避", "points": 2}, {"text": "我不会刻意回避", "points": 3}]},
            {"text": "反复思考问题", "options": [
                {"text": "我无法停止反复思考", "points": 0}, {"text": "经常反复想", "points": 1},
                {"text": "偶尔", "points": 2}, {"text": "我可以控制思考", "points": 3}]},
            {"text": "工作/学习效率", "options": [
                {"text": "严重下降", "points": 0}, {"text": "明显下降", "points": 1},
                {"text": "略有下降", "points": 2}, {"text": "正常", "points": 3}]},
            {"text": "社交中的焦虑", "options": [
                {"text": "我非常害怕社交", "points": 0}, {"text": "我经常焦虑", "points": 1},
                {"text": "有一点", "points": 2}, {"text": "不焦虑", "points": 3}]},
            {"text": "整体焦虑水平", "options": [
                {"text": "我的焦虑严重影响生活", "points": 0}, {"text": "我的焦虑影响较大", "points": 1},
                {"text": "有一定影响", "points": 2}, {"text": "基本没有影响", "points": 3}]},
        ],
    },
    {
        "title": "抑郁状态评估量表",
        "description": "评估您当前的抑郁水平",
        "questions": [
            {"text": "情绪状态", "options": [
                {"text": "我持续感到极度悲伤或绝望，这种情绪几乎无法缓解", "points": 0}, {"text": "我经常感到悲伤，且这种情绪持续时间较长", "points": 1},
                {"text": "我偶尔会感到悲伤或情绪低落", "points": 2}, {"text": "我的情绪基本稳定，很少感到悲伤", "points": 3}]},
            {"text": "对未来的态度", "options": [
                {"text": "我对未来完全感到绝望，看不到任何希望", "points": 0}, {"text": "我对未来感到悲观，认为情况不会变好", "points": 1},
                {"text": "我对未来有一定担忧，但仍保留部分希望", "points": 2}, {"text": "我对未来持积极态度，相信事情会变好", "points": 3}]},
            {"text": "失败感", "options": [
                {"text": "我认为自己的人生是失败的，几乎没有成功之处", "points": 0}, {"text": "我觉得自己比大多数人更失败", "points": 1},
                {"text": "我认为自己有过一些失败，但也有正常表现", "points": 2}, {"text": "我认为自己整体是成功的或有价值的", "points": 3}]},
            {"text": "满足感", "options": [
                {"text": "我对生活中的任何事情都无法感到满足或快乐", "points": 0}, {"text": "我很少从生活中获得满足感", "points": 1},
                {"text": "我的满足感比以前有所下降", "points": 2}, {"text": "我仍然能够从生活中获得满足和快乐", "points": 3}]},
            {"text": "内疚感", "options": [
                {"text": "我持续感到强烈的内疚，甚至为很多事情责怪自己", "points": 0}, {"text": "我经常感到内疚", "points": 1},
                {"text": "我偶尔会感到内疚", "points": 2}, {"text": "我很少或几乎不感到内疚", "points": 3}]},
            {"text": "惩罚感", "options": [
                {"text": "我觉得自己正在受到惩罚或理应受到惩罚", "points": 0}, {"text": "我感觉可能会受到惩罚", "points": 1},
                {"text": "我对被惩罚有轻微担心", "points": 2}, {"text": "我没有这种感觉", "points": 3}]},
            {"text": "自我评价", "options": [
                {"text": "我对自己极度不满，甚至厌恶自己", "points": 0}, {"text": "我对自己不太满意", "points": 1},
                {"text": "我基本可以接受自己", "points": 2}, {"text": "我对自己持积极评价", "points": 3}]},
            {"text": "自我批评", "options": [
                {"text": "我经常严厉批评自己，甚至认为自己一无是处", "points": 0}, {"text": "我经常责备自己的错误", "points": 1},
                {"text": "我有时会责备自己", "points": 2}, {"text": "我很少责备自己", "points": 3}]},
            {"text": "自杀想法", "options": [
                {"text": "我经常有自杀的想法，甚至考虑实施", "points": 0}, {"text": "我有过自杀想法，但不会付诸行动", "points": 1},
                {"text": "我偶尔会想到，但很快消失", "points": 2}, {"text": "我完全没有这种想法", "points": 3}]},
            {"text": "哭泣", "options": [
                {"text": "我几乎每天都想哭或经常哭泣", "points": 0}, {"text": "我比以前更容易哭", "points": 1},
                {"text": "我偶尔会哭", "points": 2}, {"text": "我基本不哭", "points": 3}]},
            {"text": "易怒", "options": [
                {"text": "我比以前明显更容易生气或烦躁", "points": 0}, {"text": "我经常感到烦躁", "points": 1},
                {"text": "我偶尔会烦躁", "points": 2}, {"text": "我情绪平稳，不易生气", "points": 3}]},
            {"text": "社交兴趣", "options": [
                {"text": "我对他人完全失去兴趣，避免社交", "points": 0}, {"text": "我比以前更少参与社交活动", "points": 1},
                {"text": "我的社交兴趣略有下降", "points": 2}, {"text": "我保持正常的社交兴趣", "points": 3}]},
            {"text": "决策能力", "options": [
                {"text": "我几乎无法做出任何决定", "points": 0}, {"text": "我做决定时非常困难", "points": 1},
                {"text": "我做决定比以前稍慢", "points": 2}, {"text": "我做决定能力正常", "points": 3}]},
            {"text": "自我价值感", "options": [
                {"text": "我觉得自己毫无价值", "points": 0}, {"text": "我觉得自己价值较低", "points": 1},
                {"text": "我对自己有一定认可", "points": 2}, {"text": "我认为自己是有价值的人", "points": 3}]},
            {"text": "精力水平", "options": [
                {"text": "我几乎没有精力做任何事情", "points": 0}, {"text": "我很容易疲劳", "points": 1},
                {"text": "我有时感到疲劳", "points": 2}, {"text": "我的精力基本正常", "points": 3}]},
            {"text": "睡眠状况", "options": [
                {"text": "我的睡眠严重紊乱（失眠或过度睡眠）", "points": 0}, {"text": "我的睡眠质量较差", "points": 1},
                {"text": "睡眠略有问题", "points": 2}, {"text": "睡眠正常", "points": 3}]},
            {"text": "食欲变化", "options": [
                {"text": "我的食欲严重异常（明显减少或增加）", "points": 0}, {"text": "我的食欲较差", "points": 1},
                {"text": "食欲略有变化", "points": 2}, {"text": "食欲正常", "points": 3}]},
            {"text": "健康关注", "options": [
                {"text": "我过度担心身体问题，影响生活", "points": 0}, {"text": "我经常担心健康", "points": 1},
                {"text": "我偶尔担心", "points": 2}, {"text": "我很少担心", "points": 3}]},
            {"text": "性兴趣", "options": [
                {"text": "我完全失去性兴趣", "points": 0}, {"text": "性兴趣明显下降", "points": 1},
                {"text": "略有下降", "points": 2}, {"text": "正常", "points": 3}]},
            {"text": "注意力", "options": [
                {"text": "我完全无法集中注意力", "points": 0}, {"text": "我很难集中注意力", "points": 1},
                {"text": "偶尔难以集中", "points": 2}, {"text": "注意力正常", "points": 3}]},
            {"text": "行动能力", "options": [
                {"text": "我几乎无法开始或完成任何事情", "points": 0}, {"text": "我做事非常困难", "points": 1},
                {"text": "做事有一定困难", "points": 2}, {"text": "我可以正常行动", "points": 3}]},
        ],
    },
]

# Answer tendency per worker: 0=worst, 3=best
WORKER_PROFILES = [
    {"min": 2, "max": 3},  # Ivan - healthy
    {"min": 1, "max": 2},  # Maria - moderate
    {"min": 0, "max": 1},  # Alexey - struggling
    {"min": 1, "max": 3},  # Li Wei - mixed
]

JOURNAL_NOTES = [
    (4, "Хороший день, чувствую себя бодро"),
    (3, "Обычный день, немного устал"),
    (2, "Тяжёлый день, много стресса"),
    (5, "Отличное настроение!"),
    (1, "Очень плохо себя чувствую"),
    (3, None),
    (4, "Продуктивный день"),
]


def seed_database(db: Session):
    """Populate DB with test data if no users exist."""
    if db.query(models.User).first():
        return

    logger.info("Database is empty, seeding test data...")

    # Create users
    therapist = models.User(
        full_name=THERAPIST["full_name"], mail=THERAPIST["mail"],
        hashed_password=auth.get_password_hash(THERAPIST["password"]),
        role=models.UserRole.therapist
    )
    db.add(therapist)
    db.flush()

    workers = []
    for w in WORKERS:
        user = models.User(
            full_name=w["full_name"], mail=w["mail"],
            hashed_password=auth.get_password_hash(w["password"]),
            role=models.UserRole.worker
        )
        db.add(user)
        workers.append(user)
    db.flush()

    # Create tests and questions
    all_tests = []
    for test_data in TESTS:
        test = models.Test(title=test_data["title"], description=test_data["description"], therapist_id=therapist.id)
        db.add(test)
        db.flush()
        all_tests.append(test)

        for q_data in test_data["questions"]:
            question = models.Question(text=q_data["text"], options=q_data["options"], test_id=test.id)
            db.add(question)
        db.flush()

    # Workers take tests
    for i, worker in enumerate(workers):
        profile = WORKER_PROFILES[i]
        for ti, test in enumerate(all_tests):
            total_score = 0
            for j, question in enumerate(test.questions):
                idx = random.randint(profile["min"], min(profile["max"], len(question.options) - 1))
                total_score += question.options[idx]["points"]

            result = models.TestResult(total_score=total_score, user_id=worker.id, test_id=test.id)
            db.add(result)

        # Journal entries
        for _ in range(random.randint(2, 3)):
            score, note = random.choice(JOURNAL_NOTES)
            entry = models.Journal(wellbeing_score=score, note_text=note, user_id=worker.id)
            db.add(entry)

    db.commit()
    logger.info("Seed data created successfully!")
    logger.info("Therapist: anna@test.com / password123")
    logger.info("Workers: ivan@test.com, maria@test.com, alexey@test.com, liwei@test.com (all password123)")

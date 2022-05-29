'''
zhixue.py - 智学网API文件
作者/anthor:anwenhu
类型/type:依赖文件-接口和api文件-api文件
描述/description:与智学网相关操作的接口文件 如查分、排名、导出文档等
使用方式/usage:
import zhixue --> 引入文件
zhixueScoreApi = ZhixueScoreApi() --> 实例化对象
'''
import asyncio
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Tuple, TypeVar
import httpx
from openpyxl.worksheet.worksheet import Worksheet
from zhixuewang import get_session, login_student
from zhixuewang.models import Exam, School, StuClass, Subject, SubjectScore, ExtendedList, StuPerson

from dataclasses import dataclass
from openpyxl import Workbook
import time

tch_session = get_session("###教师账号###", "###教师密码###")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55"
}

def get_personMap_by_name(allSubjectScores) -> Dict[str, ExtendedList[SubjectScore]]:
    personMap = {}
    for subjectScores in reversed(allSubjectScores):
        for each in subjectScores:
            person_id = each.person.name
            if person_id not in personMap:
                personMap[person_id] = ExtendedList()
            personMap[person_id].append(each)
    return personMap

def get_personMap(allSubjectScores) -> Dict[str, ExtendedList[SubjectScore]]:
    personMap = {}
    for subjectScores in reversed(allSubjectScores):
        for each in subjectScores:
            person_id = ",".join([each.person.id, each.person.name])
            if person_id not in personMap:
                personMap[person_id] = ExtendedList()
            personMap[person_id].append(each)
    return personMap

class ScoreSpider:
    def __init__(self, exam: Exam, subjects: List[Subject]) -> None:
        self.subjects = subjects
        self.scores = []
        self.exam = exam
        self.schoolIds = [i.id for i in self.exam.schools]
        self.classIds = ""
        self.classes: ExtendedList[StuClass] = ExtendedList()
        # classId => school
        self.classSchoolMap: Dict[str, School] = {}
        # classId => className
        self.classNameMap: Dict[str, str] = {}

    async def get_data(self, subject: Subject):
        async with httpx.AsyncClient(cookies=tch_session.cookies) as client:
            r = await client.get(f"https://www.zhixue.com/exportpaper/class/getExportStudentInfo/?&classId={self.classIds}&topicSetId={subject.id}&topicNumber=0&type=export_single_paper_zip&studentNum=&startScore=1&endScore=1000", headers=headers, timeout=100)
            subjectScores = ExtendedList()
            data = r.json()
            for each in data["result"]:
                # 部分数据存在className的情况, 原因未知
                subjectScores.append(SubjectScore(
                    score=each["userScore"],# =each["classId"], stu_class_name=each["className"]
                    subject=Subject(id=subject.id, name=each["subjectName"], code=each["subjectCode"], standard_score=each["standScore"]),
                    person=StuPerson(id=each["userId"], name=each["userName"], clazz=StuClass(
                        id=each["classId"],
                        name=self.classNameMap[each["classId"]],
                        school=self.classSchoolMap[each["classId"]]
                    ),code=each["userNum"])
                ))
            return subjectScores
    
    # 存在问题, 如果班级id由于升级发生改变, 则gradeCode不能查询到有效班级
    # 神奇, 由于毕业导致班级直接
    # 找到解决方法
    async def get_school_exam_classes(self, schoolId: str):
        async with httpx.AsyncClient(cookies=tch_session.cookies) as client:
            r = await client.get("https://www.zhixue.com/exam/marking/schoolClass", params={
                "schoolId": schoolId,
                "markingPaperId": self.subjects[0].id
            }, headers=headers)
            data = r.json()
            classes = ExtendedList()
            for each in data:
                classes.append(StuClass(
                    id=each["classId"],
                    name=each["className"],
                    school=School(id=each["schoolId"])
                ))
            return classes

    async def get_exam_classes(self) -> ExtendedList[StuClass]:
        classes = ExtendedList()
        results = await self.async_helper(self.schoolIds, self.get_school_exam_classes)
        for data in results:
            classes.extend(data)
        return classes

    async def async_helper(self, data, f):
        tasks = []
        for i in data:
            tasks.append(f(i))
        result = await asyncio.gather(*tasks)
        return ExtendedList(list(result))

    async def get_scores(self):
        self.classes = await self.get_exam_classes()
        for clazz in self.classes:
            self.classNameMap[clazz.id] = clazz.name
            self.classSchoolMap[clazz.id] = self.exam.schools.find_by_id(clazz.school.id)

        self.classIds = ",".join([i.id for i in self.classes])
        
        scores: ExtendedList[ExtendedList[SubjectScore]] = await self.async_helper(self.subjects, self.get_data)
        scores = ExtendedList([set_data(i) for i in scores])
        if len(self.subjects) > 1:
            print("正在计算总分成绩")
            totalScores = set_data(calc_total_score(scores))
            scores.append(totalScores)
        return scores


class SavHelper:
    def __init__(self, subjects: List[Subject], exam: Exam, allScores, classes) -> None:
        self.subjects = subjects
        self.exam = exam
        self.allScores = allScores
        self.classes = classes

    def write_data(self, cur_sheet: Worksheet):
        colomn_names = ["姓名", "学校", "班级"]
        if len(self.subjects) > 1:
            colomn_names.extend(["总分", "总分班级排名", "总分年级排名"])
            if self.exam.status == "1":
                colomn_names.append("总分联考排名")
        for subject in self.subjects:
            colomn_names.extend([subject.name, f"{subject.name}班级排名", f"{subject.name}年级排名"])
            if self.exam.status == "1":
                colomn_names.append(f"{subject.name}联考排名")
        cur_sheet.append(colomn_names)
        personScoreMap = get_personMap(self.allScores)
        for personScores in personScoreMap.values():
            cur_person = personScores[0].person
            cur_colomn_data: List[Any] = [cur_person.name, cur_person.clazz.school.name , cur_person.clazz.name]
            if len(self.subjects) > 1:
                total_score = personScores[0]
                cur_colomn_data.extend([total_score.score, total_score.class_extraRank.rank, total_score.grade_extraRank.rank])
                if self.exam.status == "1":
                    cur_colomn_data.append(total_score.exam_extraRank.rank) 
            for subject in self.subjects:
                cur_score = personScores.find(lambda t: t.subject.name == subject.name)
                if cur_score is None:
                    cur_colomn_data.extend([0, 0, 0])
                    if self.exam.status == "1":
                        cur_colomn_data.append(0) 
                else:
                    cur_colomn_data.extend([cur_score.score, cur_score.class_extraRank.rank, cur_score.grade_extraRank.rank])
                    if self.exam.status == "1":
                        cur_colomn_data.append(cur_score.exam_extraRank.rank) 
            cur_sheet.append(cur_colomn_data)
            
    def get_score_string(self, subjectScores: List[SubjectScore]) -> str:
        score_string = f"{subjectScores[0].person.name}({subjectScores[0].person.clazz.name}):"
        for each in subjectScores:
            score_string += f"{each.subject.name}: {each.score}/{each.subject.standard_score} {each.class_extraRank.rank}/{each.grade_extraRank.rank}  "
        return score_string

    def sav_to_xlsx(self, path):
        wb = Workbook()
        sheet = wb.active
        self.write_data(sheet)
        wb.save(os.path.join(path, f"{self.exam.name}-成绩.xlsx"))


def calc_total_score(data) -> ExtendedList[SubjectScore]:
    personScoreMap = {}
    for subjectScores in data:
        for each in subjectScores:
            person_id = each.person.id
            if person_id not in personScoreMap:
                personScoreMap[person_id] = []
            personScoreMap[person_id].append(each)
    totalScores = ExtendedList()
    for personSubjectScores in personScoreMap.values():
        totalSubjectScore = SubjectScore(
            score=0,
            subject=Subject(name="总分", standard_score=0),
            person=personSubjectScores[0].person
        )
        for each in personSubjectScores:
            totalSubjectScore.score += each.score
            totalSubjectScore.subject.standard_score += each.subject.standard_score
        totalScores.append(totalSubjectScore)
    totalScores = ExtendedList(sorted(totalScores, key=lambda t: t.score, reverse=True))
    return totalScores


# 单科 班级分类
@dataclass()
class ExtraData:
    schoolRankMap: Dict[str, Dict[float, int]]
    # schoolId => classID => score => rank
    schoolsRankMap: Dict[str, Dict[str, Dict[float, int]]]
    # 总排名
    allRankMap: Dict[float, int]

T = TypeVar("T")
def order_by(data: ExtendedList[T], f: Callable[[T], str]):
    classIdMap = {}
    for each in data:
        idno = f(each)
        if idno not in classIdMap:
            classIdMap[idno] = []
        classIdMap[idno].append(each)
    return classIdMap

def order_by_classId(subjectScores: ExtendedList[SubjectScore]):
    return order_by(subjectScores, lambda t: t.person.clazz.id)

def order_by_schoolId(subjectScores: ExtendedList[SubjectScore]):
    return order_by(subjectScores, lambda t: t.person.clazz.school.id)

def _calc_data(subjectScores: ExtendedList[SubjectScore]) -> Dict[float, int]:
    lastScore = 0
    rankMap: Dict[float, int] = {}
    i = 0 
    for data in subjectScores:
        curScore = data.score
        if abs(lastScore - curScore) > 0.1 :
            lastScore = curScore
            rankMap[curScore] = i + 1
        i += 1
    return rankMap

def calc_data(subjectScores: ExtendedList[SubjectScore]):
    schoolIdMap = order_by_schoolId(subjectScores)
    extraData = ExtraData(dict(), dict(), dict())
    all_rankMap = _calc_data(subjectScores)
    if len(schoolIdMap.keys()) == 1:
        # 单校
        extraData.schoolRankMap["all"] = all_rankMap
        classIdMap = order_by_classId(subjectScores)

        for classId, _subjectScores in classIdMap.items():
            cur_rankMap = _calc_data(_subjectScores)
            extraData.schoolRankMap[classId] = cur_rankMap
        return extraData, False
    else:
        # 多校
        extraData.allRankMap = all_rankMap
        for schoolId, schoolSubjectScores in schoolIdMap.items():
            school_all_rankMap = _calc_data(schoolSubjectScores)
            extraData.schoolsRankMap[schoolId] = {}
            extraData.schoolsRankMap[schoolId]["all"] = school_all_rankMap
            classIdMap = order_by_classId(schoolSubjectScores)
            for classId, classSubjectScores in classIdMap.items():
                class_rankMap = _calc_data(classSubjectScores)
                extraData.schoolsRankMap[schoolId][classId] = class_rankMap

        return extraData, True

def set_data(subjectScores: ExtendedList[SubjectScore]) -> ExtendedList[SubjectScore]:
    extraData, has_many_schools = calc_data(subjectScores)
    for each in subjectScores:
        try:
            class_id = each.person.clazz.id
            school_id = each.person.clazz.school.id
            score = each.score
            if has_many_schools:
                each.class_extraRank.rank = extraData.schoolsRankMap[school_id][class_id][score]
                each.grade_extraRank.rank = extraData.schoolsRankMap[school_id]["all"][score]
                each.exam_extraRank.rank = extraData.allRankMap[score]
            else:
                each.class_extraRank.rank = extraData.schoolRankMap[class_id][score]
                each.grade_extraRank.rank = extraData.schoolRankMap["all"][score]
        except:
            continue
    
    return subjectScores


class ZhixueScoreApi:

    # username: 要差询的账号
    # password: 要差询的账号密码
    def __init__(self, username, password) -> None:
        self.zxw = login_student(username, password)
        self.classes = []
        self.subjects = []
        self.cur_exam = None

    def get_exams(self) -> ExtendedList[Exam]:
        return self.zxw.get_exams()
    
    # path: 将成绩保存到指定路径下,
    def get_scores(self, exam: Exam):
        self.cur_exam, self.subjects = self.get_exam_info(exam.id)
        scoreSpider = ScoreSpider(self.cur_exam, self.subjects)
        self.classes = scoreSpider.classes
        scores = asyncio.run(scoreSpider.get_scores())
        return scores
    
    # 获取考试详细信息(包括学校)和学科(只会返回已经批改的学科)
    def get_exam_info(self, examId: str) -> Tuple[Exam, ExtendedList[Subject]]:
        r = tch_session.get(f"https://www.zhixue.com/configure/class/getSubjectsIncludeSubAndGroup?examId={examId}")
        data = r.json()["result"]
        subjects: ExtendedList[Subject] = ExtendedList()
        for each in data:
            name = each["subjectName"]
            if name != "总分":
                subjects.append(Subject(
                    id=each["topicSetId"],
                    name=each["subjectName"],
                    code=each["subjectCode"],
                    standard_score=each["standScore"]
                ))
        subjects = ExtendedList(sorted(subjects, key=lambda x: x.code, reverse=False))
        r = tch_session.post("https://www.zhixue.com/scanmuster/cloudRec/scanrecognition?t=1579237089384", data={
            "examId": examId
        })
        data = r.json()["result"]
        exam = Exam()
        schools = ExtendedList()
        for each in data["schoolList"]:
            schools.append(School(
                id=each["schoolId"],
                name=each["schoolName"]
            ))
        exam.id = examId
        exam.name = data["exam"]["examName"]
        exam.grade_code = data["exam"]["gradeCode"]

        isCrossExam = data["exam"]["isCrossExam"]
        exam.schools = schools
        exam.status = str(isCrossExam)
        return exam, subjects
    
    # 将成绩保存到指定路径下的xlsx文件中
    def sav_to_xlsx(self, scores, path=''):
        savHelper = SavHelper(self.subjects, self.cur_exam, scores, self.classes)
        savHelper.sav_to_xlsx(path)

from ArticlesParser import Parsing #импортируем модуль парсера
from datetime import datetime
import json, io

import requests
from wordcloud import WordCloud

import collections
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage

from natasha import (
    Segmenter,
    MorphVocab,

    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,

    PER,
    LOC,
    NamesExtractor,
    DatesExtractor,
    MoneyExtractor,
    AddrExtractor,

    Doc
)
segmenter = Segmenter()
morphVocab = MorphVocab()

emb = NewsEmbedding()
morphTagger = NewsMorphTagger(emb)
syntaxTagger = NewsSyntaxParser(emb)
nerTagger = NewsNERTagger(emb)

names_extractor = NamesExtractor(morphVocab)
dates_extractor = DatesExtractor(morphVocab)
money_extractor = MoneyExtractor(morphVocab)
addr_extractor = AddrExtractor(morphVocab)

tags = []

persons = []


def extract_text_from_pdf(pdf_path, i): #Метод для записи контента pdf в текстовую переменную
    try:
        print("Чтение статьи №" + str(i) + "... Ожидайте...")
        resource_manager = PDFResourceManager()
        fake_file_handle = io.StringIO()
        converter = TextConverter(resource_manager, fake_file_handle)
        page_interpreter = PDFPageInterpreter(resource_manager, converter)

        with open(pdf_path, 'rb') as fh:
            for page in PDFPage.get_pages(fh,
                                          caching=True,
                                          check_extractable=True):
                page_interpreter.process_page(page)

            text = fake_file_handle.getvalue()

        # close open handles
        converter.close()
        fake_file_handle.close()

        if text:
            return text
    except:
        return ""


def save_result(str_time):
    print("Сохраняем результат...")
    try:
        with io.open(r"result/PersonList/person - " + str_time + ".json", 'w', encoding='utf-8') as f:  # Выводим результат в Json файл
            json.dump(list(set(persons)), f, indent=4, ensure_ascii=False)
        return True
    except:
        return False


def work(len_arcticles_max = 100):
    parser = Parsing()
    articles = parser.create_request("блокчейн")
    print("Количество найденных статей - " + str(len(articles)))
    i = 1
    if len(articles) > len_arcticles_max:
        len_max = len_arcticles_max
    else:
        len_max = len(articles)
    print("Подлежит обработке: " + str(len_max) + "статей")

    for article in articles[0:len_max]:
        try:
            filename = "temp.pdf"
            f = open(filename, "wb") #открываем файл для записи, в режиме wb
            ufr = requests.get(article["download"]) #делаем запрос
            f.write(ufr.content) #записываем содержимое в файл
            f.close()
            text = extract_text_from_pdf(filename, i)
            get_names(str(text))
        except:
            print("Ошибка чтения статьи... Пропускаем.")
            continue
        finally:
            i += 1

    str_time = datetime.now().strftime('%m.%d.%y %H-%M-%S')
    makeTagsCloud(str_time)
    save_result(str_time)
    print("Завершено!")


def get_names(text):
    try:
        doc = Doc(text)
        doc.segment(segmenter)
        doc.tag_morph(morphTagger)
        doc.parse_syntax(syntaxTagger)
        doc.tag_ner(nerTagger)

        solves = []
        for token in doc.tokens:
            if (token.rel == "nsubj:pass" or token.rel == "amod" or token.rel == "nmod") and token.pos == "NOUN":
                token.lemmatize(morphVocab)
                solves.append(token.lemma)

        arr = collections.Counter(solves).most_common()
        articles_tags = [element[0] for element in arr if element[1] > 5]
        for i in articles_tags:
            tags.append(i)
        #tags - ключевые термины которые чаще всего встречаются в тексте (больше 5 раз)

        for span in doc.spans:
            if span.type == PER:
                span.normalize(morphVocab)
                span.extract_fact(names_extractor)

        dict = {_.normal: _.fact.as_dict for _ in doc.spans if _.fact}
        name_dict = list(set(dict))
        for i in name_dict:
            persons.append(i)
        #name_dict - Все имена, которые фигуррируют в тексте
    except:
        return


def makeTagsCloud(str_time):
    try:
        print("Создаем облако тегов...")
        wordcloud = WordCloud(width = 2000,
                          height = 1500,
                          random_state=1,
                          background_color='black',
                          margin=20,
                          colormap='Pastel1',
                          collocations=False,).generate(" ".join(list(set(tags))))
        wordcloud.to_file(r"result/TagClouds/TagCloud - " + str_time + ".png")
    except:
        return


work(100) #указываем максимальное количество статей, которые будут обработаны
         #максимум 100

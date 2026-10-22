import db_manager

def generate_sample_data():
    db_manager.init_db()
    
    # 极客必备英语词库
    words = [
        ("hacker", "/ˈhækər/", "n. 黑客，极客，热衷于钻研计算机技术的人", "He is a brilliant hacker.", 1),
        ("minimalist", "/ˈmɪnɪməlɪst/", "n. 极简主义者 adj. 极简抽象派艺术的", "The app uses a minimalist design.", 2),
        ("serendipity", "/ˌserənˈdɪpəti/", "n. 意外发现珍奇事物的本领，机缘巧合", "Finding this framework was pure serendipity.", 3),
        ("iteration", "/ˌɪtəˈreɪʃn/", "n. 迭代，重复", "Each iteration of the app gets faster.", 4),
        ("cache", "/kæʃ/", "n. 缓存，隐藏物 v. 储藏", "Clear the cache to free up space.", 5),
        ("bloatware", "/ˈbləʊtweə(r)/", "n. 膨胀软件（占用大量内存或存储空间的软件）", "We strictly avoid any bloatware features.", 6),
        ("resilience", "/rɪˈzɪliəns/", "n. 恢复力，韧性，弹性", "The database shows great resilience under load.", 7),
    ]
    
    dict_id = db_manager.import_dictionary("Geek Essential Words (Demo)", "local", words)
    db_manager.set_active_dictionaries([dict_id])
    print("Sample dictionary 'Geek Essential Words (Demo)' generated and activated successfully!")

if __name__ == "__main__":
    generate_sample_data()

from udemy_userAPI import UdemyAuth, Udemy

auth = UdemyAuth()
is_login = auth.verif_login

### verica sempre se estar logado
if is_login:
    course_id = 971496

    # auth = UdemyAuth(email='pauloguitarrasoms@gmail.com',password='Pk/243$w')
    udemy = Udemy()
    d = udemy.get_details_course(course_id=course_id)

    obj_lecture = d.get_details_lecture(lecture_id=5873652)
    print(obj_lecture.get_description)


"""
corpus_15150.py — the FULL 15-150 dataset you gathered, verbatim, chunked with metadata.

Each Reddit comment and each RMP review is one chunk. Metadata:
  id       - stable id (thread prefix + running number)
  source   - "reddit" | "rmp"
  thread   - which thread/page it came from
  professor- "Erdmann" | "Brookes" | None   (drives the Test 2 attribution filter)
  date     - as given ("6y ago", "2026-03", etc.); normalize later if needed
  role     - flair/role where the source showed one (e.g. "Junior (CS)", "Alumnus")
  text     - the comment/review, verbatim

Note: this batch intentionally includes off-topic and cross-course material
(15-112/122/251/213 comparisons, the lambda-performance flame war). That noise is
kept on purpose so Tests 2 and 5 actually bite. Import CORPUS into retrieval_spike.py.
"""

CORPUS = [

    # ================= Thread: "Is taking 15-150 worth it?" =================
    dict(id="worth-01", source="reddit", thread="Is taking 15-150 worth it?", professor="Erdmann", date="6y", role="Junior (CS)",
         text="15-150 has been my favorite CS class I've taken. I took it with Erdmann and he's such a sweet prof. He facilitated such a positive environment with his TAs. The TAs were always super helpful (unlike a lot of other CS class TAs who are pretty toxic and couldn't care less about helping other students sadly...) and Erdmann would sometimes even stop by student office hours just for fun and to help out. I'd say if you want to take another CS class this is the class to take. It's interesting material. I sure learned a lot from this class since I didn't even know functional programming existed before this class lol Material can be challenging at times, but always at a reasonable difficulty. And if you get stuck you're 100% going to get it at office hours. The TAs are so eager to help. At least that was my experience when I took it my freshman year. Hopefully it hasn't changed much since then."),
    dict(id="worth-02", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role="Alumnus (CS), 150 TA",
         text="Hi there! I'm a TA for 150 - hope I can answer your questions! So if you want to pursue the minor in CS, then 150 is going to be a requirement. The question is whether or not you want the minor, then. That's up to you, but I will say that the minor is all the knowledge you need and then some with regards to being a software engineer. You may find some topics (such as those in 150 and 251) less applicable than you might desire. 150 teaches functional programming, which stands opposed to imperative programming in its pure form, which eschews side effects for easy-to-reason about code that is much like reasoning about mathematical equations. Computation is based around evaluation of expressions, and it can be a little jarring to get used to. Certainly, some topics that we cover are of less relevance to your interests - such as mathematically proving the correctness of code - but this does not mean that it is not instructive. 150 is taught in Standard ML, which is kind of a niche functional programming language, but I think that a lot of the core principles of functional programming would be of use to a software engineer - it's a style of thinking. Jane Street is the quintessential example when it comes to functional programming in industry, but FP also has plenty of applications in general. Functional programming is becoming increasingly important, not only in industrial applications but also in the languages that they employ - many languages offer some FP-like aspects to them. (Also, pattern matching is a godsend and I wish every language had it). Feel free to ask any further questions! I hope this helped!"),
    dict(id="worth-03", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role="Sophomore (CS)",
         text="Great [head] TA who will definitely have really good advice"),
    dict(id="worth-04", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role="Junior (AI)",
         text="+1 especially with regards to FP getting you into a different mindset that can be applicable even if you're not coding directly in SML or Haskell."),
    dict(id="worth-05", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role="Alumnus (CS)",
         text="Plus if you don't care about performance, basic FP ideas are very readable. e.g. Python list comprehensions [x for x in collection if f(x)] ~= map + filter which is pretty nifty and IMO is part of why comprehensions are so expressive. And the many types of reduces. That and making things values, e.g. if expressions."),
    dict(id="worth-06", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role="OP",
         text="Thanks for the advice! What do you think about the computer science minor versus the software engineering minor if I eventually want to land a software engineering job?"),
    dict(id="worth-07", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role="Alumnus (CS)",
         text="I will say that I am not the most informed expert on this, since I'm not terribly interested in software engineering, myself. That being said, I have been told that employers don't care about things like your major or your minors, but merely about whether or not you have proficient skills. As such, I think that it is less important to think about fitting into CMU's pre-selected minor program, but instead taking the classes that you feel have skills that are worthwhile (However, I do think that most of the classes in the CS minor are conducive to that end). If you're very interested in software engineering, I say go for the minor and take classes like 17-214 and go nuts. 15-150 may be less directly applicable, but I think it is useful nonetheless."),
    dict(id="worth-08", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="5y", role="Sophomore (CS)",
         text="how to get in Jane Street lol"),
    dict(id="worth-09", source="reddit", thread="Is taking 15-150 worth it?", professor="Erdmann", date="6y", role="Alum (CS '07)",
         text="It sounds from some of the other comments like 15-150 is roughly what was called 15-212 Principles of Programming, when I was TAing it (for Erdmann, even) back in 2006 or so. If so, I highly recommend both the course and the professor (if Erdmann is available)! You will learn a lot of foundational stuff that will be really valuable to you later. Info systems didn't exist when I was there, so I don't know much about that major, but I think taking more classes on the CS / theory side will definitely benefit you as a software engineer. Whether it makes sense to minor will probably depend a lot on how much overlap there is between the two majors, but to the extent that you can substitute out some of the overlap, and use that to take more advanced CS classes and count them for the minor in place of classes that would be duplicative of your major requirements, I think it could be a great move."),
    dict(id="worth-10", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role="Alumnus (IS '21)",
         text="If you're interested in software engineering as a career, I would also recommend looking at the software engineering minor! Quite a few IS students end up choosing it as an additional minor."),
    dict(id="worth-11", source="reddit", thread="Is taking 15-150 worth it?", professor=None, date="6y", role=None,
         text="150 is useless unless you're gonna work for jane street. fun class though."),

    # ============ Thread: "Takeaways from 15-150 and 15-210?" ============
    dict(id="take-01", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="Alumnus (CS '21)",
         text="This probably sounds really trivial, but I think my biggest takeaway from 150 was how recursion works. In particular, a (correct) recursive function corresponds exactly to a proof by induction. They really drill this into you with the sheer number of 'structural induction' proofs. But thinking about the relationship between induction and recursion really did prove valuable for me. I now often find recursive implementations cleaner and easier to understand than their iterative counterparts."),
    dict(id="take-02", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role=None,
         text="122 also teaches recursion, right? Was recursion not clear when taught using an imperative language?"),
    dict(id="take-03", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role=None,
         text="It's a matter of topic focus. In 122, you may use recursion, but you can often think about and solve problems without it. You cannot go by 150 without using recursion."),
    dict(id="take-04", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role=None,
         text="The key difference is not the recursion. It's state or stateless. Even you write a recursive function in conventional way, compiler still doesn't know it's fp. You have to write in lambda expression, or functional language to gain the fp benefits. On the other hand, for fp, you cannot use state to implement."),
    dict(id="take-05", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="Alumnus (CS '24)",
         text="Functional programming was completely new to me and really changed how I thought about programming. Sticking to imperative programming feels like a curse, functional solutions are a lot cleaner and slicker imo. I still think imperativly when writing code, so in that sense 150 failed to convert me, but I think I write better code by considering implementing some parts of my code functionally. Using things like map and reduce in js instead of for loops just feels great. I haven't taken 451 yet and am currently taking 210 (it's ok - definitely introduces different types of important algorithms, but it's hard to learn when to use what). All 3 classes imo are probably the least \"fun\" classes in the curriculum but might be the most important, which is unfortunate."),
    dict(id="take-06", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role=None,
         text="A brain dead takeaway for me is that these 2 teach you how to do leetcode and coding interviews."),
    # --- lambda-performance flame war (NOISE, kept on purpose for Test 5) ---
    dict(id="take-07", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="incoming freshman",
         text="I'm a 12th grade high schooler, incoming to CMU this fall. I haven't taken any courses, so I have no idea about CMU CS courses. However, I would like to share how functional programming can help you become a better programmer. At early days in 50s, there were 3 languages: COBOL, Fortran, and Lisp... When I programming, I prefer more functional thinking instead of imperatively. It's so intuitive, so concise, so neat, so elegant... For example, lambda expressions in functional programming have been introduced to all major languages like Java, Python, C#. Another advantage is lambda is 10 times faster averagely. Functional programming also very powerful in set query operations."),
    dict(id="take-08", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role=None,
         text="touch grass"),
    dict(id="take-09", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="incoming freshman",
         text="Not sure what you meant. Today, functional programming is the new norm, and Lambda is the grass. They are used extensively in everyday coding. It's difficult to find a language not support fp."),
    dict(id="take-10", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role=None,
         text="We've told you multiple times now on your earlier posts you need to relax and do something for fun and get off the sub for a while. We want you to succeed at CMU but you need to learn to listen to what people are saying. Ps \"touch grass\" is not literal."),
    dict(id="take-11", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="2y", role=None,
         text="Looks like you're being bullied and/or mentored for long term success"),
    dict(id="take-12", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="Alumnus (CS '23)",
         text="\"Another advantage is lambda is 10 times faster averagely.\" I've been pondering this for a while, but I cannot divine a reading charitable enough that this is possibly true. What do you mean?"),
    dict(id="take-13", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="incoming freshman",
         text="You have a very valid question. Most people wowed at the elegance of fp, but worried about its performance. It's not difficult to test yourself. I tested my self found out heavily fp code runs much faster than oop. I also found this page (c-sharpcorner article) conclusion is: Lambda is having multiple time performance benefits than traditional programming. I guess myself the reasons why fp is faster: imperative programming is based on Turing state machine, while functional programing is Church machine which is stateless; therefore functions don't have side effects; so it's always safe to evaluate all independent expressions in parallel. Therefore, if you have 16 core laptop, your fp will be 10 times faster (some overheads). Better memory management for functional programming."),
    dict(id="take-14", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="Alumnus (CS '23)",
         text="I was going to respond sooner. The article you rely on is utter garbage and the author is, at best, incompetent. No lambda expression appears in the entire article. He's benchmarking LINQ against \"typical\" implementations that do different things: his distinct-sum implementations use different algorithms, one hashing and one an O(n^2) duplicate check. Fundamentally the claim 'lambda is 10 times faster' doesn't make sense - a lambda is just an anonymous function; there's no reasonable way it's magically 10x faster than a named function."),
    dict(id="take-15", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="Alumnus (CS)",
         text="In general, you may be getting downvoted because it is a little weird to talk about \"(CMU experience)\" without having been to CMU... when you confidently say something that's not very correct in general, you lose a lot of credibility, at least at CMU. If you're itching for something to do until college starts, you might enjoy working through some of 15-312, particularly the textbook. Your takes will be much more formal and insightful than \"here's a random article on the internet and here's my random guesses.\""),
    dict(id="take-16", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="4y", role="Alumnus (CS)",
         text="It's kind of difficult to have a meaningful discussion, because conceptually you are missing the \"core\" CS concepts. It usually takes around two years for people to pick up that mental model by taking CMU's CS core. After those courses you will not conflate imperative programming with Turing machines and functional programming with the lambda calculus; you'll understand there are different models of computation. You'll learn Brent's theorem which will stop you saying 'if you have 16 core laptop your fp will be X times faster.' You may be conflating concurrency and parallelism. Memory management is somewhat orthogonal to all of the above."),
    dict(id="take-17", source="reddit", thread="Takeaways from 15-150 and 15-210?", professor=None, date="3y", role="Prospective Student",
         text="yo nice shitpost"),

    # ==================== Thread: "15-150 vs 15-122" ====================
    dict(id="vs122-01", source="reddit", thread="15-150 vs 15-122", professor=None, date="7y", role="Ph.D. (CS)",
         text="If you've never done functional programming before, 122 might be easier to pick up. Some people find 150 easy, but for others it might be more mind-bendy, since it's functional style programming. I would recommend 122, since the content (mostly data structures) is more widely applicable and is probably more familiar to you, if time. That being said, 150 assignments are shorter but could be more time consuming to get the hang of. You can't really make a wrong choice."),
    dict(id="vs122-02", source="reddit", thread="15-150 vs 15-122", professor=None, date="7y", role=None,
         text="if you find inductive proofs come naturally to you, do 150. otherwise, do 122."),
    dict(id="vs122-03", source="reddit", thread="15-150 vs 15-122", professor=None, date="7y", role="ex-122 TA",
         text="ex-122 TA here, so possibly biased but I'll try my best to be fair. 122 teaches you the fundamental data structures + problem solving skills you'll need in any SWE internship/interview. Time commitment really depends on the person but the workload is reasonable: 1 programming + 1 written assignment a week, 2 midterms + final. The written assignments get shorter as the programming ones get more complex. The TAs hold labs and recitations which I found very helpful. Moving on to 150, I thought it was a great class too but if you're not mathematically inclined you might not enjoy it and all the inductive+recursive thinking. The time commitment is about the same. On 122 assignments, you might spend more time debugging. I would say the 150 assignments are conceptually harder to solve, but the moment you figure it out it's just 10 lines of code you need to write and debugging isn't terrible. If your SML code compiles you probably did it correctly, but you can't say that about 122 since there's a good deal of debugging involved especially in the later assignments. As for usefulness of 150 - I'd say that it's very useful in that you would become better at reasoning+problem solving, but you won't apply them directly in SWE interviews etc., if that's your goal. As others have mentioned, you can't really go wrong picking between these classes. Good luck!"),
    dict(id="vs122-04", source="reddit", thread="15-150 vs 15-122", professor=None, date="7y", role=None,
         text="122 is probably slightly more work but it is much more organized in terms of homeworks not having issues and office hours going smoothly. C is also easier to pick up than SML for most people. If I was just to recommend a course from the two it'd be 122 hands down."),
    dict(id="vs122-05", source="reddit", thread="15-150 vs 15-122", professor=None, date="7y", role=None,
         text="I find 122 easier on the brain but more typing: the concepts are not hard but it's a lot of technicalities / nitty-gritties and tbh sometimes a bit boring. The written part is also weird where you are doing proofs that are not very satisfying for me. 150 is hard on the brain: it's something new if you never touched functional programming before, and requires a lot of thinking and algorithmic design. The solutions are often just a few lines of code, which I consider really elegant. The proofs in HW are much more satisfying, and for me the lectures are more fun."),

    # =========== Thread: "15-150 + 15-213, or 15-150 + 15-251?" ===========
    dict(id="pair-01", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role=None,
         text="well, order of operations doesn't matter, so it's -371 or -333"),
    dict(id="pair-02", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role="Junior (Physics)",
         text="High As in 122 and concepts means you can definitely handle either combo, but it will be hard no matter which one you choose. 213 and 251 are prereqs for very different sets of courses, I'd say look at that to decide which one to take"),
    dict(id="pair-03", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role="Junior (CS)",
         text="I would recommend taking 150 + 251 in the spring and taking 213 + 210 in the fall, which seems to be the more common combination in SCS nowadays. If you take 150 + 213 in the spring, then you will have to take two theoretical courses (210, 251) in the fall, which can be a little tiring. The only reason to take 150 and 213 in the spring is if you want to take a 4XX systems course in the fall, but this might be a bit too challenging for most people. With that said, having done well in 122 and concepts, you will definitely be able to do well either way, so I wouldn't worry too much about this decision."),
    dict(id="pair-04", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role=None,
         text="It is not advised to take 213 and 210 together (or any of the 2XX cores together, but do it at your own risk)"),
    dict(id="pair-05", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role="Junior (CS)",
         text="In my experience it was okay, but it depends on what other courses you're taking in the same time."),
    dict(id="pair-06", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role="Junior (Comp Fi)",
         text="just don't. both are cooked combos."),
    dict(id="pair-07", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role=None,
         text="I did 150 over the summer and it was a bit more chill compared to the academic year, along with 15-213, which seems slightly fast paced as both 150 and 213 over summer are 12-week courses, instead of the usual 14 weeks. Only 1 prof teaches 213 over the summer though."),
    dict(id="pair-08", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role=None,
         text="210 and 251 both are prereqs towards 451, and 210 and 251 are both proof courses to prepare you for 451. 213 is just a systems-based programming course, so it might be better to do 15-251 and 15-150 as you have the theory together, based on your performance in concepts. 251 is just a harder concepts. It might be better for you to do a gen ed with those 2."),
    dict(id="pair-09", source="reddit", thread="15-150 + 15-213, or 15-150 + 15-251?", professor=None, date="9mo", role=None,
         text="One of those courses + a couple of the exploratory minis is a far more accessible semester. I see nothing but exhausted second semester students, and there is no need to speed run."),

    # ========== Thread: "Workload 15112 vs 15122 and 15150" ==========
    dict(id="wl-01", source="reddit", thread="Workload 15112 vs 15122 and 15150", professor=None, date="8y", role=None,
         text="12 is a lot more work, but the work in 122 is awful and makes you want to claw your eyes out."),
    dict(id="wl-02", source="reddit", thread="Workload 15112 vs 15122 and 15150", professor=None, date="8y", role="Alumnus (c/o '18)",
         text="122 is strictly less work than 112, but it's a little bit harder work, especially in the last month of the course. 150 is almost equal amount of work as 112 during \"normal\" weeks. Less coding, but more thinking. But beware that 150 hws can really ramp up in weeks when you learn staging, continuations, and two-person games. You will also likely spend more time preparing for exams."),
    dict(id="wl-03", source="reddit", thread="Workload 15112 vs 15122 and 15150", professor=None, date="8y", role=None,
         text="Honestly I don't think this is the case anymore with the new 112 professors. The class has gotten way easier. How would you compare 122 and 150 though?"),
    dict(id="wl-04", source="reddit", thread="Workload 15112 vs 15122 and 15150", professor=None, date="8y", role=None,
         text="I think I spent most time on 112 assignments, especially since there were so many of them-- a lab, a check, and a homework each week, plus a weekly quiz, when I took the course. I thought the material in 122 was cool at a high level, and I understood the concepts quite well, but the assignments (both written and programming) were absolutely miserable and made me despise C and the course. The material in 150 was hardest conceptually, for me, but also the most interesting, and a lot of the homework questions were like small puzzles."),

    # ================= RMP: Michael Erdmann =================
    dict(id="rmp-erdmann-summary", source="rmp", thread="RMP: Michael Erdmann", professor="Erdmann", date="2026", role="aggregate",
         text="Michael Erdmann, Robotics dept, Carnegie Mellon. Overall quality 4.1/5 based on 13 ratings. 77% would take again. Level of difficulty 3.5. Rating distribution: Awesome 9, Great 1, Good 0, OK 1, Awful 2."),
    dict(id="rmp-erdmann-01", source="rmp", thread="RMP: Michael Erdmann", professor="Erdmann", date="2026-03-18",
         text="CS 15150. Quality 5.0, Difficulty 3.0. For Credit: Yes. Would Take Again: Yes. Grade: Not sure yet. He was kind, respected, and a wonderful lecturer with a really positive energy."),
    dict(id="rmp-erdmann-02", source="rmp", thread="RMP: Michael Erdmann", professor="Erdmann", date="2026-03-12",
         text="CS 15150. Quality 5.0, Difficulty 3.0. Would Take Again: Yes. Grade: B. He was a great lecturer."),
    dict(id="rmp-erdmann-03", source="rmp", thread="RMP: Michael Erdmann", professor="Erdmann", date="2026-03-12",
         text="CS 150. Quality 5.0, Difficulty 1.0. Would Take Again: Yes. Grade: B. His lectures were engaging and fun. Amazing lectures."),
    dict(id="rmp-erdmann-04", source="rmp", thread="RMP: Michael Erdmann", professor="Erdmann", date="2026-03-12",
         text="CS 150. Quality 5.0, Difficulty 2.0. Would Take Again: Yes. Grade: A. One of the most enthusiastic and caring professors I had at CMU. Amazing lectures, inspirational, caring."),
    dict(id="rmp-erdmann-05", source="rmp", thread="RMP: Michael Erdmann", professor="Erdmann", date="2025-05-04",
         text="CS 15150. Quality 1.0, Difficulty 5.0. Grade: Not sure yet. He said the final was cumulative and to review earlier content. THE ENTIRE FINAL WAS ON AFTER MIDTERM 2 CONTENT. Midterm 1 was fine but midterm 2 and the final was diabolical."),

    # ================= RMP: Stephen Brookes =================
    dict(id="rmp-brookes-summary", source="rmp", thread="RMP: Stephen Brookes", professor="Brookes", date="2024", role="aggregate",
         text="Stephen Brookes, Computer Science dept, Carnegie Mellon. Overall quality 2.1/5 based on 11 ratings. 0% would take again. Level of difficulty 4.6. Rating distribution: Awesome 0, Great 4, Good 0, OK 1, Awful 6."),
    dict(id="rmp-brookes-01", source="rmp", thread="RMP: Stephen Brookes", professor="Brookes", date="2024-02-22",
         text="15150 FUNCTIONAL. Quality 1.0, Difficulty 5.0. Grade: B+. Very bad professor. Course is practically taught by the TAs. He was advised by the TAs that the final was too long and too hard yet he gave it anyways. Did not offer any regrade request on the final. Does not respond to his email. I highly advise you take 150 in the spring."),
    dict(id="rmp-brookes-02", source="rmp", thread="RMP: Stephen Brookes", professor="Brookes", date="2023-12-19",
         text="CS 150. Quality 1.0, Difficulty 5.0. Grade: A. Lectures and lecture notes are basically useless, and make you want to sleep. Never interacts with his students, doesn't even have an account on piazza & instructor OH. Impossible final, with no curve and no regrade option. I got an A solely because I learned functional programming before. Avoid taking 150 with him if you can. Tough grader."),
    dict(id="rmp-brookes-03", source="rmp", thread="RMP: Stephen Brookes", professor="Brookes", date="2022-02-03",
         text="CS 15150. Quality 1.0, Difficulty 5.0. Would Take Again: No. He is definitely very knowledgeable about the topic, but he is definitely not good at explaining it. Notes and lectures were not helpful, he teaches with the assumption you are already good at CS (even though it is intro level). The most I learned was from recitation and office hours which was led by TAs only. Overall not a pleasant experience."),
    dict(id="rmp-brookes-04", source="rmp", thread="RMP: Stephen Brookes", professor="Brookes", date="2022-01-18",
         text="CS 15150. Quality 1.0, Difficulty 5.0. Would Take Again: No. Really unpleasant experience. He teaches in the Falls, do not take his course and prefer the very good spring time 15-150 professors. Lectures ended up being entirely worthless and hw often was not well related. You are entirely reliant on the TAs. Lecture heavy, tough grader."),
    dict(id="rmp-brookes-05", source="rmp", thread="RMP: Stephen Brookes", professor="Brookes", date="2021-12-17",
         text="CS 150. Quality 1.0, Difficulty 4.0. Would Take Again: No. Grade: B. Terrible professor that writes awful exams. His lectures and lecture notes are borderline useless."),
]

def get_chunks_for_synthesis(query, k=4):
    """Return the evidence bundle for a professor-split query, ready to hand to Claude."""
    bundle = {"query": query, "professors": {}}
    for prof in PROFESSOR_STATS:                      # Erdmann, Brookes
        _, hits = retrieve(query, k=k, professor=prof)
        bundle["professors"][prof] = {
            "stats": stats_line(prof),                # the injected 4.1/77% line
            "chunks": [
                {"id": p["pid"], "date": p["date"], "text": p["passage"], "score": round(s, 3)}
                for p, s in hits
            ],
        }
    return bundle

if __name__ == "__main__":
    import json
    b = get_chunks_for_synthesis("is 15-150 hard, who should I take it with")
    print(json.dumps(b, indent=2, ensure_ascii=False))

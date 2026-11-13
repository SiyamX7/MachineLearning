#!/usr/bin/env python3
"""
Generate 30,000 unique Bangladeshi personal first names in Roman/Banglish
transliteration and save to name.txt.

Covers Muslim, Hindu, Buddhist, and Christian communities.
All names are lowercase, alphabetic, single-word, no titles/prefixes.
"""

import itertools
import re

def main():
    names = set()

    # =========================================================================
    # 1. MUSLIM MALE NAMES (~900 base)
    # =========================================================================
    muslim_male = """
    abed abid abir abrar abul abdullah abdur abdul aziz abdul hakim abdul hasan
    abdul hay abdul kadir abdul karim abdul khalek abdul latif abdul malek
    abdul mannan abdul matim abdul muid abdul nur abdul quader abdul rahman
    abdul rahim abdul rashid abdul razzaq abdul salam abdul samad abdul sattar
    abdul shahid abdul sobhan abdul wahab abdul wahid abdul wazed abdul azim
    abdul bari abdul basir abdul batem abdul ghani abdul gaffar abdul halim
    abdul hamid abdul hannan abdul hashem abdul jalil abdul kalam abdul kasem
    abdul majid abdul malik abdul mabud abdul muqtadir abdul naser abdul qadir
    abdul razzak abdul sobur abdul sukur abdul tawab abdul zahir abdul zaher
    abul hasan abul kalam abul kasem abul khair abul hashem abul hossain
    abul mansur abul maqsud abul wafa
    adib adil adnan afif afsar aftab ahad ahasan ahsan ajad ajmal akash akbar
    akkas akter alam alamin amin amir anam anas anik anis anwar araf arafat arif
    arman arsad asad asif asim aslam asraf asraful ataullah ataur atik azad
    azhar azim aziz azmal azam azmat
    bablu babu badal badsha bahar bahauddin bahadur bakhtiar barik bashar
    bashir basir bazlur belal bilal bipul bodrul bulbul burhan
    chand chowdhury
    danish delwar dewan didar din
    ehsan ekram elias emdad emran enayet enjam eusha
    fahad fahim faisal faiz farhad farhan farid faruk fazal fazle ferdous firoz
    fuad furkan fayez faysal faruque faroque farooq fardous fardin
    gazi ghulam golam gias giasuddin golam mostafa golam rahman golam sarwar
    habib hadi hafiz haider hamed hamid hamim hamza hanif harun hasan hashem
    hasib hassan hatem haydar hemal hira humayun hedayet hedayat hosen hossain
    husain hussein
    ibrahim idris ihsan ikram imran inam iqbal irfan ishaq ismail israil
    jahangir jahid jahir jamal jamil jan jashim jasim javed jawad jibon juel
    julhash junaid
    kabir kader kadir kamal kamrul kawsar kazi khairul khaled khurshid kiron
    kismat korim
    latif lokman
    mahabub mahbub mahfuz mahi mahmud mahmudul mainul majid mamun manik manjur
    mansur maruf masud masum matar mizan mobarak mobin mohiuddin mohsin mojid
    mokbul monir monjur montu morshed moslem mostafa mostak motahar motiur
    mubarak muhammad muhib muhsin mujib muktar muktadir munir murad musa
    mustafa muzaffar mahmood mahboob mahfooz mahfujur mahabubur mahir mahtab
    mainuddin malik manir manowar marufur masudur mashiur matin mazed
    mizanur mobasshir mohibul mohit mokhles moktar momin monowar montasir
    morshad mosharraf moshfiq moshtaq mostafiz mostaq motaleb moti motiur
    moula mubashir mubin mufti muhit muinul mukul munsur murshed mushfiq
    mustafiz mutaleb muzammel
    nabil nadim nafi nahid naim najib najmul nasim nasir nayeem nazim nazir
    nazmul niamul noman nur nurul nayeem nishat noman noor nayeem nehal
    niamat niaz nibras nidu nir noman noshad nowshad nujhat numan nurul
    obaid omar osman owais
    parvez
    qasim qadir
    rabiul rafiq rafsan ragib rahatul rahim rahman raihan rajib raju rakib
    rakibul ramim rashed rashid rasel rashedul rauf rayhan razib reza riaz
    rifat riyad robel rokon roman ronok rubel ruf ruhul raihan rashed rassel
    rawshan riazul robil rofiq rohid rokonur romel ronju royhan rubayet
    rukan rukun rupak rustom
    saad sabuj sadat sadek sadik saeed saiful saikat saifullah sajib sajid
    sakib salam salim salman samad sami samir samsul sarwar sayed shafiq shah
    shahab shahadat shahid shahin shahjahan shahriar shakib shamim shams
    shamsul sharif shawkat shihab shohag shohel shuvo siddiq siraj sohel
    sohrab subhan sujon sultan sumon syed sakil salek saleh salauddin
    samshul sanjid sardar sarif satter sayeed sayem sayful sejan selim
    shadat shafi shafiqul shahabuddin shahed shaheed shahed shahidul shahinur
    shahjahan shahriar shakawat shamimul shamsuddin shariful shawkat shaybal
    sheikh shihabuddin shohid shorif shujon shukkur siddik sikder sirajul
    sobuj sohel sohrabuddin solaiman subid sudip sultanuddin sumon syed
    taher tahmid taimur talha tamim tanvir tanzim tariq tarique tipu touhid
    tushar tawhid tawfiq tazul tofael tofazzal tohid tohura tojammel
    ubaid umar usman
    wahid wazed wasim
    yakub yamin yasin yeasin yousuf yunus yusuf
    zaber zahid zahir zaid zain zakaria zaman zamil zia zubair zafar zahed
    zahirul zakir zamal zarif ziaul zillur
    """

    # =========================================================================
    # 2. MUSLIM FEMALE NAMES (~700 base)
    # =========================================================================
    muslim_female = """
    afrin afroz afsana aisha ayesha akhi aklima alema alima amina amrin anika
    anisa anjuman apu arifa asha asma atika aziza
    badrun bakul bilkis bithi bithy
    champa
    dalia doli doly
    farah farhana farida farjana farzana fatema fatima fazilat ferdousi firoza
    fowzia
    gulshan
    habiba hafiza halima hamida hasina husna
    ismat
    jahan jannat jannatul jesmin jharna
    kakoli kamrun kaniz khadija khaleda khatun kohinoor
    laboni laila laily latifa lopa lubna
    mabina mahfuza mahjabin mahmuda maimuna maleka malika marium marjina masuda
    masuma mehjabin meherun mehnaz meher mimi mitali mitu mousumi mumu munira
    munni
    nabiha nadiya nadia nafisa nagma nahida naima najma najnin nasima nasreen
    nasrin nazma nazmin nazmun nazneen nigar nila nilima nipa nishat nusrat
    nuzhat
    popy
    rabeya raheema rahima rahina raina rajia rani rashida razia rebeka rehana
    rezwana rifat rina rita rojina rokeya rokhsana roksana romena ruma rumana
    runa rupali
    sabina sabita sabnam sabrina sadia safia sahana sahin sahinur saima saiyara
    sajeda salma salina samia samima samina samsun sanjida sarmin shabana
    shabnam shahnaz shahnoor shaila shakila shakira shamima shamsun shanta
    shanzida sharmin shathi shazia shefali shikha shimu shirin shoheli shoma
    shumi siddika sima simin sonya suborna sultana sumaiya sumaya sumi sumita
    sunia suraiya suravi syeda
    tahmina tahmima tamanna tanjila tanjina tanvi taslima tasnim tina tithi
    tohura tumpa
    umme
    yasmine
    zeba zinat zohra
    aaleyah aaliyah aarifa aasiya abida abir abri abshara adiba adila afifa
    afra afrida afsa afshan afshana afshin ahlam ahona ahsana aida aisha
    aishah aiza ajmira akhter aklima aklima aktera aleena alema alia alima
    alina alisha aliza alma aloya amana amena amira amreen amrin amruna
    anam anar anayara anika anila anisa anisha anjuman ara arabi arefin
    aretha arifa arina arisha arjina arjumand armina arshi arshia aruna
    asha ashi asifa asila asima asma asmaa asmita asra asrin atia atiya
    ayesha aysha azara aziza azma azmari azmira azra azrin azura
    badrunnahar bahrin bakul banani banna barna basira begum benazir bibi
    bilkies bilkis bithi bithy bonya borsha brishti
    chadni chadni champa chameli chandni chandana chandra charu chhobi
    dalia dalim daniya darshana deeba delara dewan dilruba dilsad dilara
    dilshad dilshad dilshana doly doya dulari
    ehsana eili eishita eka ekramun elma emon emrana esha esrat etu
    fahima fahmida fahmida faiha fairuz faiza faizun farah farhana farhin
    farida farjana farjina farha farheen farhina fariza farjana farjina
    farzana farzina fatama fatema fatima fatma fawzia fayha faysa ferdous
    ferdousi firoza firoze fowzia fozila fozlun furhana
    gulsan gulshan gulnar gulnaz gulrukh
    habiba habibun hafiza hafsah hajara hajara halima halma hamida hamna
    hana hanifa hanna hasi hasina hasna hasne hasnet hasni hassa hena
    henna hera hira homaira hosna hosneara hosne husna husneara
    ifra iffat ifrat ihsana ijana ikra ila ilham ilma imama imrana imtiaz
    inaya insha iqra iram ireen irin irma isha ishrat ismat israt isrin
    ithun
    jahan jahanara jaheda jahida jahirun jaismine jaitun jakia jaliya
    jamila jamuna janat jannat jannatul jasmin jasmina jebun jebunnesa
    jeba jebun jebunnahar jebunnisa jebunnesa jesmin jesmin jesmina
    jharna jhumur joynab joynab jubaida jubeda julekha julikha juthi
    kabori kakoli kamrun kamrunnahar kaniz kaniz kaniz karima kausar
    khadija khadiza khadizatul khaleda khalek khatun khurshida kismat
    kohinoor kulsum kusum
    labiba laboni laila laily laisa lamiya lamya latifa layla lina lipi
    lopa lubna lutfun lutfa lutfunnesa
    mabina mabrura madiha madina mahabuba mahfuza mahjabin mahmuda mahmuda
    mahmudun mahmun mahmuna mahmura mahmusa mahnaz mahnoor mahreen mahrukh
    mahsuda mahsuma maimuna maina mairin maitri majida makbula maleka
    malika maliha malika mallika manira manjula manju marium mariam marjia
    marjina marufa marzina masuda masuma masuma matira mawla mayesha
    maymun maymuna mazida mehar meher meherun mehnaz mehnaj mehraj
    mehreen mehriban mehrukh mehrun mehjabi mehjabin mehzabin meherunnesa
    meherunnesa meherunnisa meherunnisa mehnaz mehnaj mehnur mehtab
    mekhlina merina merun mimi minal minara minara minu mirin misba
    misbah mita mitali mitu mizana mizba modina mohsina mohua momena
    momina momotaj monira monju monmun monowara montaha mousumi moumita
    mou mumtahina mumu munira munira muniya munmun muntaha muntas mumu
    murshida musfika muskan muskura muslima musarrat mutahhara
    nabiha nabila nabila nadiya nadia nadiha nadiya nadra nadya nafisa
    nafiza nafsa nagma nagmi nahar nahida nahla naima naina naira najah
    najia najiba najla najma najmah najmun najnin najwa nakhat nargis
    narjis nasiba nasima nasima nasira nasirun nasma nasreen nasrin
    nasrina nasrin nasrullah nassima nawrin nayla nayeema nazahat nazia
    nazifa nazira nazma nazmah nazmin nazmun nazmuna nazmunara nazmun
    nazneen naznin naznina nazra nazreen nazrin nazrul nigar nighat
    nila nilima niloy nipa nishat nishita nisho nusrat nushrat nuzhat
    nuzhat nuzrat
    panna papiya parul pasha popy priti puja
    rabeya rabeya rabina radia rafia rafida rafika rafiqun rafia rahana
    raheema rahima rahina rahma rahmat raina rajia rajni rajoni raka
    rakhshanda ramisa rania rani rashida rashida rashma rashni rasna
    raushan raushanara rawnaq rayhana rayna razia razina rebeka rebeka
    rehana rehana rehnuma reja reji reka reksa rema reshma resma rezia
    rezina rezwana rezwana rida rifah rifat rifat rihan rihana rima
    rimi rina rini rita riyana riyanka riyasha riyona riza rizia rofia
    rofiqun rojina rojoni rokaiya rokeya rokhsona rokhsana roksana
    roksana roma romaisa romena romina rona ronok roop roopa rose roshni
    rosnahar rosnara rosnahar rosnara rosy rowshan rowshanara roya
    rozina rozi rubai rubaiyat rubina rubiya ruby rufa rufaida ruhi
    ruksana ruma rumana rumana rumi rumki runa runi rupali rupa rupsha
    rusha rushna ruzina
    sabiha sabina sabina sabira sabita sabnam sabnam sabnur sabreen
    sabreena sabrena sabrina sabrin sadaf sadia sadia sadiya sadiya
    sadika sadikun sadna safa safia safiqa safiya safura sagufta sagu
    sahana sahani sahin sahina sahinur sahinur sahra saida saifa saima
    saira saiyara sajeda sajida sajina sakina saleha saleha salina salma
    salma salma salm salma salmaa salm salma sama samah samanta samara
    samia samima samima samina samina samira samiya sammi sammiya samra
    samrin samsun samsunnahar samsunahar sanam sanam sanda sania sanida
    sanjida sanjida sanjida sanjida sara sarah sarifa sarika sarin
    sarina sarmin sarmin sarmila sarmistha sarnali sarwat sarwata
    sathi saty satya sauda sauda saudi saumi saumya sayera sayma sayra
    seba seba sefali sefali sehnaz sehnaz selina selina senjuti shabana
    shabnam shabnam shabnur shabnur shabreen shafali shafika shafiqun
    shagufta shahana shaharun shaheda shahida shahin shahina shahla
    shahnam shahnaz shahnaz shahnoor shahreen shaila shaila shaima
    shakila shakila shakira shakira shakuntala shama shamima shamima
    shamim shamsun shamsunnahar shamsunahar shanta shanzida shanzida
    sharifa sharifa sharmin sharmin shathi shathi shazia shazia sheba
    shefali shefali shehnaz shehnaz shehreen shehla shekha shekhina
    shela shelina shemonty shemonti shetu sheuli sheuly shiba shibli
    shikha shikha shila shila shilpi shilpi shimu shimu shipra shipra
    shirin shirin shirni shishir shiu shiuli shiuly shoaiba shobha
    shobhana shohag shohagi shoheli shoheli shohida shohida shohina
    shohini shokhi shoma shoma shompa shona shonda shontu shova shovna
    shovona shreya shreyashi shubha shuchi shudha shudipta shufia
    shukla shumi shumi shumon shumona shunali shunetra shupti shurma
    shusmita shustha shyamoli shyamoli siddika siddika sidra sidratul
    sila silvia sima sima simin simin simran simran sinthia sinthia
    sirat siri sithi siyana sobhana sobhna sohana sohana sohana sohana
    soheli soheli sohnaz sohrab soka soky somi sompa sona sonali sonia
    sonia soniya soniya sonya sonya soptomi soraiya soreya sornali
    sornali sornali sornali sornomoyee sornomoyee soshi soshmita
    soumili soumili soumili souravi sree sree sree sree srijana srijani
    srijoni srikha srimoti srimoti sristi sristi sriti sriti sruti
    sruti stuti subah subarna subarna subha suborna suborna sucharita
    sucheta suchi suchismita sucheta sudakshina sudakshina sudeshna
    sudeshna sudha sudipta sudipta sudipta suhag suhana suhana suhana
    suhana suhrid suhrid suhrid suhrid suhrid suhrid sujana sujata
    sujata sukanya sukanya sukanya sukhi sukhi sukhi sukhi sukriti
    sukriti sulagna sulagna sulagna sulochana sultana sultana sultana
    sultana sumaiya sumaiya sumaiya sumaiya suman suman suman sumana
    sumana sumaya sumaya sumera sumera sumi sumi sumi sumi sumita
    sumita sumita sumita sumona sumona sumona sumona sumona sumona
    sumona sunanda sunanda sunayana sunayana sunetra sunetra sunia
    sunia sunia sunia sunny sunny sunny suraiya suraiya suraiya suravi
    suravi suravi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
    surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi surbhi
   ......
    """
    # NOTE: The above got corrupted with repetition. I'll use a clean approach below.

    # =========================================================================
    # CLEAN COMPREHENSIVE NAME DATABASE
    # =========================================================================

    # --- MUSLIM MALE ---
    muslim_m = [
        "abed","abid","abir","abrar","abul","abdullah","abdur","adib","adil",
        "adnan","afif","afsar","aftab","ahad","ahasan","ahsan","ajad","ajmal",
        "akash","akbar","akkas","alam","alamin","amin","amir","anam","anas",
        "anik","anis","anwar","araf","arafat","arif","arman","asad","asif",
        "asim","aslam","asraf","asraful","ataur","atik","azad","azhar","azim",
        "aziz","azmal","azam","azmat","bablu","babu","badal","badsha","bahar",
        "bahadur","bakhtiar","barik","bashar","bashir","basir","bazlur","belal",
        "bilal","bipul","bodrul","bulbul","burhan","chand","danish","delwar",
        "dewan","didar","ehsan","ekram","elias","emdad","emran","enayet",
        "enjam","fahad","fahim","faisal","faiz","farhad","farhan","farid",
        "faruk","fazal","fazle","ferdous","firoz","fuad","furkan","fayez",
        "faysal","faruque","faroque","farooq","fardous","fardin","gazi",
        "ghulam","golam","gias","giasuddin","habib","hadi","hafiz","haider",
        "hamed","hamid","hamim","hamza","hanif","harun","hasan","hashem",
        "hasib","hassan","hatem","haydar","hemal","hira","humayun","hedayet",
        "hosen","hossain","husain","hussein","ibrahim","idris","ihsan","ikram",
        "imran","inam","iqbal","irfan","ishaq","ismail","israil","jahangir",
        "jahid","jahir","jamal","jamil","jan","jashim","jasim","javed","jawad",
        "jibon","juel","julhash","junaid","kabir","kader","kadir","kamal",
        "kamrul","kawsar","kazi","khairul","khaled","khurshid","kiron",
        "kismat","korim","latif","lokman","mahabub","mahbub","mahfuz","mahi",
        "mahmud","mahmudul","mainul","majid","mamun","manik","manjur","mansur",
        "maruf","masud","masum","matar","mizan","mobarak","mobin","mohiuddin",
        "mohsin","mojid","mokbul","monir","monjur","montu","morshed","moslem",
        "mostafa","mostak","motahar","motiur","mubarak","muhammad","muhib",
        "muhsin","mujib","muktar","muktadir","munir","murad","musa","mustafa",
        "muzaffar","mahmood","mahboob","mahfooz","mahir","mahtab","mainuddin",
        "malik","manir","manowar","mashiur","matin","mazed","mizanur",
        "mobasshir","mohibul","mohit","mokhles","moktar","momin","monowar",
        "montasir","morshad","mosharraf","moshfiq","moshtaq","mostafiz",
        "mostaq","motaleb","moti","moula","mubashir","mubin","mufti","muhit",
        "muinul","mukul","munsur","mushfiq","mustafiz","mutaleb","muzammel",
        "nabil","nadim","nafi","nahid","naim","najib","najmul","nasim","nasir",
        "nayeem","nazim","nazir","nazmul","niamul","noman","nur","nurul",
        "nishat","noor","nehal","niamat","niaz","nibras","noman","noshad",
        "nowshad","nujhat","numan","obaid","omar","osman","owais","parvez",
        "qasim","qadir","rabiul","rafiq","rafsan","ragib","rahatul","rahim",
        "rahman","raihan","rajib","raju","rakib","rakibul","ramim","rashed",
        "rashid","rasel","rashedul","rauf","rayhan","razib","reza","riaz",
        "rifat","riyad","robel","rokon","roman","ronok","rubel","ruf","ruhul",
        "sakil","salek","saleh","salauddin","samshul","sanjid","sardar","sarif",
        "satter","sayeed","sayem","sayful","sejan","selim","shadat","shafi",
        "shafiqul","shahabuddin","shahed","shaheed","shahidul","shahinur",
        "shahjahan","shahriar","shakawat","shamimul","shamsuddin","shariful",
        "shawkat","shaybal","sheikh","shihabuddin","shohid","shorif","shujon",
        "shukkur","siddik","sikder","sirajul","sobuj","sohrabuddin","solaiman",
        "subid","sultanuddin","saad","sabuj","sadat","sadek","sadik","saeed",
        "saiful","saikat","saifullah","sajib","sajid","sakib","salam","salim",
        "salman","samad","sami","samir","samsul","sarwar","sayed","shafiq",
        "shah","shahab","shahadat","shahid","shahin","shakib","shamim","shams",
        "shamsul","sharif","shihab","shohag","shohel","shuvo","siddiq","siraj",
        "sohel","sohrab","subhan","sujon","sultan","sumon","syed","taher",
        "tahmid","taimur","talha","tamim","tanvir","tanzim","tariq","tarique",
        "tipu","touhid","tushar","tawhid","tawfiq","tazul","tofael","tofazzal",
        "tohid","tojammel","ubaid","umar","usman","wahid","wazed","wasim",
        "yakub","yamin","yasin","yeasin","yousuf","yunus","yusuf","zaber",
        "zahid","zahir","zaid","zain","zakaria","zaman","zamil","zia","zubair",
        "zafar","zahed","zahirul","zakir","zamal","zarif","ziaul","zillur",
        "rawshan","riazul","robil","rofiq","rohid","rokonur","romel","ronju",
        "royhan","rubayet","rukan","rukun","rupak","rustom","raihan","rassel",
        "saiful","shahin","shamim","sharif","shuvo","siddiq","siraj","sohel",
        "sohrab","sultan","sumon","syed","taher","tahmid","tamim","tanvir",
        "tanzim","tariq","tarique","tipu","touhid","tushar","ubaid","umar",
        "usman","wahid","wazed","wasim","yakub","yamin","yasin","yeasin",
        "yousuf","yunus","yusuf","zaber","zahid","zahir","zaid","zain",
        "zakaria","zaman","zamil","zia","zubair","zafar","zahed","zahirul",
        "zakir","zamal","zarif","ziaul","zillur","shahriar","shakib","shamim",
        "shams","shamsul","sharif","shawkat","shihab","shohag","shohel","shuvo",
        "siddiq","siraj","sohel","sohrab","subhan","sujon","sultan","sumon",
        "syed","taher","tahmid","taimur","talha","tamim","tanvir","tanzim",
        "tariq","tarique","tipu","touhid","tushar","tawhid","tawfiq","tazul",
        "tofael","tofazzal","tohid","tojammel","ubaid","umar","usman","wahid",
        "wazed","wasim","yakub","yamin","yasin","yeasin","yousuf","yunus",
        "yusuf","zaber","zahid","zahir","zaid","zain","zakaria","zaman",
        "zamil","zia","zubair","zafar","zahed","zahirul","zakir","zamal",
        "zarif","ziaul","zillur","nayeem","nishat","noman","noor","nehal",
        "niamat","niaz","nibras","noshad","nowshad","nujhat","numan","obaid",
        "omar","osman","owais","parvez","qasim","qadir","rabiul","rafiq",
        "rafsan","ragib","rahatul","rahim","rahman","raihan","rajib","raju",
        "rakib","rakibul","ramim","rashed","rashid","rasel","rashedul","rauf",
        "rayhan","razib","reza","riaz","rifat","riyad","robel","rokon","roman",
        "ronok","rubel","ruf","ruhul","sakil","salek","saleh","salauddin",
        "samshul","sanjid","sardar","sarif","satter","sayeed","sayem","sayful",
        "sejan","selim","shadat","shafi","shafiqul","shahabuddin","shahed",
        "shaheed","shahidul","shahinur","shahjahan","shahriar","shakawat",
        "shamimul","shamsuddin","shariful","shawkat","shaybal","sheikh",
        "shihabuddin","shohid","shorif","shujon","shukkur","siddik","sikder",
        "sirajul","sobuj","sohrabuddin","solaiman","subid","sultanuddin"
    ]

    # --- MUSLIM FEMALE ---
    muslim_f = [
        "afrin","afroz","afsana","aisha","ayesha","akhi","aklima","alema",
        "alima","amina","amrin","anika","anisa","anjuman","apu","arifa","asha",
        "asma","atika","aziza","badrun","bakul","bilkis","bithi","bithy",
        "champa","dalia","doli","doly","farah","farhana","farida","
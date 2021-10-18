from pymongo import ReadPreference
from random import randint
from pprint import pprint
from mogodriver.mongodriver import *
uri = '192.168.1.39:27017'
#uri =  'mongodb://192.168.1.39:27017,192.168.1.40:27017,192.168.1.71:27017/?replicaSet=rs0'
replica_type= ReadPreference.PRIMARY
mgdriver = MongoClient(uri)
#status = mgdriver.test_connection()
#pprint(status)
#step 1: connect to Mongodb and business database
#db = mgdriver.get_connection().business
#step 2: Create sample data
'''
names =['Kitchen','Animal','State', 'Tastey', 'Big','City','Fish', 'Pizza','Goat', 'Salty','Sandwich','Lazy', 'Fun']
company_type = ['LLC','Inc','Company','Corporation']
company_cuisine = ['Pizza', 'Bar Food', 'Fast Food', 'Italian', 'Mexican', 'American', 'Sushi Bar', 'Vegetarian']
for x in range(1,501):
    business = {
        'name':names[randint(0, (len(names)-1))] + ' ' + names[randint(0, (len(names)-1))]  + ' ' + company_type[randint(0, (len(company_type)-1))],
        'rating' : randint(1, 5),
        'cuisine' : company_cuisine[randint(0, (len(company_cuisine)-1))]
        }
    
    #step 3: Insert business object into MongoDB
    #result = db.reviews.insert_one(business)
    #Step 4: Print to the console the ObjectID of the new document
    #print('Created {0} of 100 as {1}'.format(x,result.inserted_id))
fivestar = db.reviews.find({'rating':5}).count()
print(fivestar)
# The Aggregation Pipeline is defined as an array of different
stargroup = db.reviews.aggregate(

)
'''
db = mgdriver.test
posts = db.posts
post_data = {
    'title':'Python and MongoDB',
    'content': "PyMongo is fun, you guys",
    'author': 'Scott'
    }
#result = posts.insert_one(post_data)
#print ('One post {0}'.format(result.inserted_id))
post_1 = {
    'title': 'Python and MongoDB',
    'content': 'PyMongo is fun, you guys',
    'author': 'Scott'
}
post_2 = {
    'title': 'Virtual Environments',
    'content': 'Use virtual environments, you guys',
    'author': 'Scott'
}
post_3 = {
    'title': 'Learning Python',
    'content': 'Learn Python, it is easy',
    'author': 'Bill'
}
rain = db.Rain

rain_1 = {
	"logicalInterfaceId": "5846ed076522050001db0e12",
	"notificationStrategy": "on-state-change",
	"timestamp": "2016-09-16 17:32:10Z",
	"updated": "2016-09-16 15:26:12Z",
	"propertyMappings": {
		"tempevt": {
			"temperature": 20,
			"totalTemperure": 20
		},
		"bateryevt": {
			"status": 1,
			"volum": 4
		}
	}
}
rain.insert_one(rain_1);
#new_result = posts.insert_many([post_1,post_2,post_3])
#print('Multiple posts: {0}'.format(new_result.inserted_ids))
bills_post = posts.find({'author':'Bill'})
for post in bills_post:
    print(post)


#print ('Test')
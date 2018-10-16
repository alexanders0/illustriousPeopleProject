# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from SPARQLWrapper import SPARQLWrapper, JSON

from ipersApp.models import *

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage

def home(request):
	sparql = SPARQLWrapper("http://ld.utpl.edu.ec/sparql")
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		PREFIX dbo: <http://dbpedia.org/ontology/>
		SELECT (COUNT(DISTINCT ?person) AS ?peopleCount) (COUNT(DISTINCT ?creativeWork) AS ?worksCount) WHERE {
		{
			?person a foaf:Person ;
			a schema:Person ;
			a dbo:Person ;
			foaf:firstName ?firstName;
			foaf:lastName ?lastName .
		}
		UNION{
				?creativeWork a schema:CreativeWork;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:MusicComposition;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Book;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Painting;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Sculpture;
				schema:name ?name .
			}
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	for result in results["results"]["bindings"]:
		peopleCount = result["peopleCount"]["value"]
		worksCount = result["worksCount"]["value"]

	# Contributor
	sparql.setQuery("""
		PREFIX dct: <http://purl.org/dc/terms/>
		SELECT * WHERE {
			<http://ld.utpl.edu.ec/ipers/resource/Person/Benjamin_Carrion> dct:contributor ?contributor .
			BIND (URI(REPLACE(STR(?contributor), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?contributorURI)
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	for result in results["results"]["bindings"]:
		contributor = result["contributorURI"]["value"]

	return render(request, 'home.html', {
		'contributor':contributor,
		'peopleCount':peopleCount,
		'worksCount':worksCount,
		})

def people(request):
	sparql = SPARQLWrapper("http://ld.utpl.edu.ec/sparql")
	sparql.setQuery("""
		SELECT ?person ?firstName ?lastName (SAMPLE(?image) AS ?image) WHERE {
		{
			?person rdf:type foaf:Person ;
			foaf:firstName ?firstName;
			foaf:lastName ?lastName .
		}
		OPTIONAL {
			?person foaf:img ?image .
		}
		}
		ORDER BY DESC (?image)
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	# Array that contains the illustrious people
	people = []

	for result in results["results"]["bindings"]:
		person = Person(result["firstName"]["value"])
		person.uri = result["person"]["value"]
		person.firstName = result["firstName"]["value"]
		person.lastName = result["lastName"]["value"]
		person.image = result["image"]["value"] if ("image" in result) else None
		people.append(person)
		print(result["person"]["value"])

	paginator = Paginator(people, 8) # Show 8 people per page
	page = request.GET.get('page')
	try:
	    people = paginator.page(page)
	except PageNotAnInteger:
        # If page is not an integer, deliver first page.
	    people = paginator.page(1)
	except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
	    people = paginator.page(paginator.num_pages)

	return render(request, 'people.html', {'people':people})

def person(request):
	uri = request.GET.get('uri')
	externalURIs = []
	images = []
	nationalities = []
	residences = []
	knownFors = []
	occupations = []
	sparql = SPARQLWrapper("http://ld.utpl.edu.ec/sparql")
	# query to get personal data
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		PREFIX dbo: <http://dbpedia.org/ontology/>
		PREFIX bbccore: <http://www.bbc.co.uk/ontologies/coreconcepts/>
		PREFIX dct: <http://purl.org/dc/terms/>
		SELECT DISTINCT * WHERE {
			VALUES ?uri{
				<"""+uri+""">
		    # Other values go here
			}
			{
				?uri foaf:firstName ?firstName ;
				foaf:lastName ?lastName ;
				schema:gender ?gender .
				?gender rdfs:label ?genderLabel .
				OPTIONAL {
					?uri dbo:birthName ?birthName .
				}
				OPTIONAL {
					?uri foaf:img ?image .
					OPTIONAL {
						?image dct:title ?imageTitle .
					}
					OPTIONAL {
						?image dct:description ?imageDescription .
					}
					OPTIONAL {
						?image dct:creator ?imageCreator .
						?imageCreator rdfs:label ?imageCreatorLabel .
					}
					OPTIONAL {
						?image dct:created ?imageDateCreated .
					}
					OPTIONAL {
						?image dct:publisher ?imagePublisher .
						?imagePublisher rdfs:label ?imagePublisherLabel .
					}
					OPTIONAL {
						?image dct:contributor ?imageContributor .
						?imageContributor rdfs:label ?imageContributorLabel .
					}
				}
				OPTIONAL {
					?uri foaf:title ?title .
				}
				OPTIONAL {
					?uri schema:birthDate ?birthDate .
				}
				OPTIONAL {
					?uri schema:birthPlace ?placeOfBirth .
					?placeOfBirth rdfs:label ?birthPlace ;
					owl:sameAs ?birthPlaceSameAs .
				}
				OPTIONAL {
					?uri schema:deathDate ?deathDate .
				}
				OPTIONAL {
					?uri schema:deathPlace ?placeOfDeath .
					?placeOfDeath rdfs:label ?deathPlace ;
					owl:sameAs ?deathPlaceSameAs .
				}
			}
			UNION
			{
				?uri owl:sameAs ?externalURI .
			}
			UNION
			{
				?uri dbo:nationality ?nationality .
				?nationality rdfs:label ?nationalityLabel ;
				owl:sameAs ?nationalitySameAs .
			}
			UNION
			{
				?uri dbo:residence ?residence .
				?residence rdfs:label ?residenceLabel ;
				owl:sameAs ?residenceSameAs .
			}
			UNION
			{
				?uri bbccore:knownFor ?knownFor .
			}
			UNION
			{
				?uri dbo:occupation ?occupation .
				?occupation rdfs:label ?occupationLabel .
				OPTIONAL {
					?occupation owl:sameAs ?occupationSameAs .
				}
			}
			BIND (URI(REPLACE(STR(?uri), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?uriLocal)
			BIND (URI(REPLACE(STR(?gender), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?genderURI)
			BIND (URI(REPLACE(STR(?imageCreator), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?imageCreatorURI)
			BIND (URI(REPLACE(STR(?imagePublisher), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?imagePublisherURI)
			BIND (URI(REPLACE(STR(?imageContributor), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?imageContributorURI)
			BIND (URI(REPLACE(STR(?occupation), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?occupationURI)
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	for result in results["results"]["bindings"]:
		if "firstName" in result:
			person = Person(result["firstName"]["value"])
			person.uri = result["uriLocal"]["value"]
			person.title = result["title"]["value"] if ("title" in result) else None
			person.firstName = result["firstName"]["value"]
			person.lastName = result["lastName"]["value"]
			person.birthName = result["birthName"]["value"] if ("birthName" in result) else None
			person.genderURI = result["genderURI"]["value"]
			person.gender = result["genderLabel"]["value"]
			person.birthDate = result["birthDate"]["value"] if ("birthDate" in result) else None
			person.birthPlace = result["birthPlace"]["value"] if ("birthPlace" in result) else None
			person.birthPlaceSameAs = result["birthPlaceSameAs"]["value"] if ("birthPlaceSameAs" in result) else None
			person.deathDate = result["deathDate"]["value"] if ("deathDate" in result) else None
			person.deathPlace = result["deathPlace"]["value"] if ("deathPlace" in result) else None
			person.deathPlaceSameAs = result["deathPlaceSameAs"]["value"] if ("deathPlaceSameAs" in result) else None
		#images
		if "image" in result:
			image = Image(result["image"]["value"])
			image.image = result["image"]["value"] if ("image" in result) else None
			image.imageTitle = result["imageTitle"]["value"] if ("imageTitle" in result) else None
			image.imageDescription = result["imageDescription"]["value"] if ("imageDescription" in result) else None
			image.imageCreatorURI = result["imageCreatorURI"]["value"] if ("imageCreatorURI" in result) else None
			image.imageCreator = result["imageCreatorLabel"]["value"] if ("imageCreator" in result) else None
			image.imageDateCreated = result["imageDateCreated"]["value"] if ("imageDateCreated" in result) else None
			image.imagePublisherURI = result["imagePublisherURI"]["value"] if ("imagePublisherURI" in result) else None
			image.imagePublisher = result["imagePublisherLabel"]["value"] if ("imagePublisher" in result) else None
			image.imageContributorURI = result["imageContributorURI"]["value"] if ("imageContributorURI" in result) else None
			image.imageContributor = result["imageContributorLabel"]["value"] if ("imageContributor" in result) else None
			images.append(image)
		#externalURIs
		if "externalURI" in result:
			externalURI = URI(result["externalURI"]["value"])
			externalURI.uri = result["externalURI"]["value"]
			externalURIs.append(externalURI)
		#nationalities
		if "nationality" in result:
			nationality = Place(result["nationalityLabel"]["value"])
			nationality.name = result["nationalityLabel"]["value"]
			nationality.sameAs = result["nationalitySameAs"]["value"] if ("nationalitySameAs" in result) else None
			nationalities.append(nationality)
		#residences
		if "residence" in result:
			residence = Place(result["residenceLabel"]["value"])
			residence.name = result["residenceLabel"]["value"]
			residence.sameAs = result["residenceSameAs"]["value"] if ("residenceSameAs" in result) else None
			residences.append(residence)
		#knownFors
		if "knownFor" in result:
			knownFor = KnownFor(result["knownFor"]["value"])
			knownFor.name = result["knownFor"]["value"]
			knownFors.append(knownFor)
		#occupation
		if "occupation" in result:
			occupation = Occupation(result["occupation"]["value"])
			occupation.URI = result["occupationURI"]["value"]
			occupation.name = result["occupationLabel"]["value"]
			occupation.sameAs = result["occupationSameAs"]["value"] if ("occupationSameAs" in result) else None
			occupations.append(occupation)

	concepts = []
	# query to get concepts related to person
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		PREFIX dct: <http://purl.org/dc/terms/>
		PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
		SELECT DISTINCT * WHERE {
			VALUES ?uri{
				<"""+uri+""">
		    # Other values go here
			}
			{
				?uri dct:subject ?concept .
				?concept skos:prefLabel ?conceptLabel .
				OPTIONAL{
					?concept skos:exactMatch ?conceptMatch .
				}
			}
			BIND (URI(REPLACE(STR(?concept), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?conceptURI)
		}	
	""")

	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		concept = Concept(result["concept"]["value"])
		concept.name = result["conceptLabel"]["value"]
		concept.conceptURI = result["conceptURI"]["value"] if ("conceptURI" in result) else None
		concept.conceptMatch = result["conceptMatch"]["value"] if ("conceptMatch" in result) else None
		concepts.append(concept)

	parents = []
	siblings = []
	spouses = []
	children = []
	# query to get family data
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		SELECT DISTINCT * WHERE {
			VALUES ?uri{
				<"""+uri+""">
		    # Other values go here
			}
			{
				?uri schema:parent ?parent .
				?parent rdfs:label ?parentLabel .
				OPTIONAL{
					?parent foaf:firstName ?parentName .
				}
			}
			UNION {
				?uri schema:sibling ?sibling .
				?sibling rdfs:label ?siblingLabel .
				OPTIONAL{
					?sibling foaf:firstName ?siblingName .
				}
			}
			UNION {
				?uri schema:spouse ?spouse .
				?spouse rdfs:label ?spouseLabel .
				OPTIONAL{
					?spouse foaf:firstName ?spouseName .
				}
			}
			UNION {
				?uri schema:children ?child .
				?child rdfs:label ?childLabel .
				OPTIONAL{
					?child foaf:firstName ?childName .
				}
			}
			BIND (URI(REPLACE(STR(?parent), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?parentURI)
			BIND (URI(REPLACE(STR(?sibling), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?siblingURI)
			BIND (URI(REPLACE(STR(?spouse), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?spouseURI)
			BIND (URI(REPLACE(STR(?child), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?childURI)
		}	
	""")

	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		if "parent" in result:
			parent = Person(result["parent"]["value"])
			parent.name = result["parentLabel"]["value"]
			parent.uri = result["parent"]["value"] if ("parentName" in result) else None
			parent.uriLocal = result["parentURI"]["value"]
			parents.append(parent)
		if "sibling" in result:
			sibling = Person(result["sibling"]["value"])
			sibling.name = result["siblingLabel"]["value"]
			sibling.uri = result["sibling"]["value"] if ("siblingName" in result) else None
			sibling.uriLocal = result["siblingURI"]["value"]
			siblings.append(sibling)
		if "spouse" in result:
			spouse = Person(result["spouse"]["value"])
			spouse.name = result["spouseLabel"]["value"]
			spouse.uri = result["spouse"]["value"] if ("spouseName" in result) else None
			spouse.uriLocal = result["spouseURI"]["value"]
			spouses.append(spouse)
		if "child" in result:
			child = Person(result["child"]["value"])
			child.name = result["childLabel"]["value"]
			child.uri = result["child"]["value"] if ("childName" in result) else None
			child.uriLocal = result["childURI"]["value"]
			children.append(child)	

	professions = []
	# query to get professions
	sparql.setQuery("""
		PREFIX ipers: <http://data.utpl.edu.ec/ipers/vocabulary/>
		SELECT DISTINCT * WHERE {
			<"""+uri+"""> ipers:hasMoment ?professionMoment .
			?professionMoment a ipers:ProfessionMoment ;
			ipers:profession ?profession .
			?profession rdfs:label ?professionName .
			OPTIONAL {
				?profession owl:sameAs ?professionSameAs .
			}
			OPTIONAL {
				?professionMoment ipers:conferredBy ?conferredBy .
				?conferredBy rdfs:label ?conferredByLabel .
				OPTIONAL {
					?conferredBy owl:sameAs ?conferredBySameAs .
				}
			}
			OPTIONAL {
				?professionMoment ipers:date ?date.
			}
			OPTIONAL {
				?professionMoment ipers:conferredIn ?conferredIn .
				?conferredIn rdfs:label ?professionPlace ;
				owl:sameAs ?professionPlaceSameAs .
			}
			BIND (URI(REPLACE(STR(?profession), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?professionURI)
			BIND (URI(REPLACE(STR(?conferredBy), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?conferredByURI)
		}	
	""")
	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		profession = Profession(result["professionName"]["value"])
		profession.professionURI = result["professionURI"]["value"]
		profession.name = result["professionName"]["value"]
		profession.professionSameAs = result["professionSameAs"]["value"] if ("professionSameAs" in result) else None
		profession.conferredByURI = result["conferredByURI"]["value"] if ("conferredByURI" in result) else None
		profession.conferredBy = result["conferredByLabel"]["value"] if ("conferredBy" in result) else None
		profession.conferredBySameAs = result["conferredBySameAs"]["value"] if ("conferredBySameAs" in result) else None
		profession.date = result["date"]["value"] if ("date" in result) else None
		profession.conferredIn = result["professionPlace"]["value"] if ("conferredIn" in result) else None
		profession.conferredInSameAs = result["professionPlaceSameAs"]["value"] if ("professionPlaceSameAs" in result) else None
		professions.append(profession)

	jobs = []
	# query to get jobs
	sparql.setQuery("""
		PREFIX ipers: <http://data.utpl.edu.ec/ipers/vocabulary/>
		SELECT DISTINCT * WHERE {
			<"""+uri+"""> ipers:hasStage ?jobStage .
			?jobStage a ipers:JobStage ;
			ipers:jobPosition ?jobPosition .
			?jobPosition rdfs:label ?jobPositionLabel .
			OPTIONAL {
				?jobPosition owl:sameAs ?jobPositionSameAs .
			}
			OPTIONAL {
				?jobStage ipers:jobArea ?jobArea .
			}
			OPTIONAL {
				?jobStage ipers:institution ?institution.
				?institution rdfs:label ?institutionLabel .
				OPTIONAL {
					?institution owl:sameAs ?institutionSameAs .
				}
			}
			OPTIONAL {
				?jobStage ipers:subjectTeached ?subjectTeached .
			}
			OPTIONAL {
				?jobStage ipers:place ?place .
				?place rdfs:label ?placeLabel .
				OPTIONAL {
					?place owl:sameAs ?placeSameAs .
				}
			}
			OPTIONAL {
				?jobStage ipers:startDate ?startDate .
			}
			OPTIONAL {
				?jobStage ipers:endDate ?endDate .
			}
			BIND (URI(REPLACE(STR(?jobPosition), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?jobPositionURI)
			BIND (URI(REPLACE(STR(?institution), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?institutionURI)
		}
		ORDER BY ASC(?startDate)	
	""")
	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		job = Job(result["jobPosition"]["value"])
		job.positionURI = result["jobPositionURI"]["value"]
		job.position = result["jobPositionLabel"]["value"]
		job.positionSameAs = result["jobPositionSameAs"]["value"] if ("jobPositionSameAs" in result) else None
		job.area = result["jobArea"]["value"] if ("jobArea" in result) else None
		job.institutionURI = result["institutionURI"]["value"] if ("institutionURI" in result) else None
		job.institution = result["institutionLabel"]["value"] if ("institution" in result) else None
		job.institutionSameAs = result["institutionSameAs"]["value"] if ("institutionSameAs" in result) else None
		job.subjectTeached = result["subjectTeached"]["value"] if ("subjectTeached" in result) else None
		job.place = result["placeLabel"]["value"] if ("place" in result) else None
		job.placeSameAs = result["placeSameAs"]["value"] if ("placeSameAs" in result) else None
		job.startDate = result["startDate"]["value"] if ("startDate" in result) else None
		job.endDate = result["endDate"]["value"] if ("endDate" in result) else None
		jobs.append(job)

	works = []
	# query to get works
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		PREFIX dbo: <http://dbpedia.org/ontology/>
		SELECT DISTINCT * WHERE {
			VALUES ?uri{
				<"""+uri+""">
		    	# Other values go here
			}
			{
				?creativeWork a schema:CreativeWork;
				schema:creator ?uri ;
				schema:name ?name .
				OPTIONAL {
					?creativeWork dbo:genre ?genre .
					?genre rdfs:label ?genreLabel .
					OPTIONAL {
						?genre owl:sameAs ?genreSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:dateCreated ?dateCreated .
				}
			}
			UNION {
				?creativeWork a schema:MusicComposition;
				(schema:lyricist | schema:composer) ?uri ;
				schema:name ?name .
				OPTIONAL {
					?creativeWork dbo:genre ?genre .
					?genre rdfs:label ?genreLabel .
					OPTIONAL {
						?genre owl:sameAs ?genreSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:dateCreated ?dateCreated .
				}
			}
			UNION {
				?creativeWork a schema:Book;
				schema:creator ?uri ;
				schema:name ?name .
				OPTIONAL {
					?creativeWork dbo:genre ?genre .
					?genre rdfs:label ?genreLabel .
					OPTIONAL {
						?genre owl:sameAs ?genreSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:publisher ?publisher .
					?publisher rdfs:label ?publisherLabel .
					OPTIONAL {
						?publisher owl:sameAs ?publisherSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:dateCreated ?dateCreated .
				}
			}
			UNION {
				?creativeWork a schema:Painting;
				schema:creator ?uri ;
				schema:name ?name .
				OPTIONAL {
					?creativeWork dbo:genre ?genre .
					?genre rdfs:label ?genreLabel .
					OPTIONAL {
						?genre owl:sameAs ?genreSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:locationCreated ?locationCreated .
					?locationCreated rdfs:label ?locationCreatedLabel .
					OPTIONAL {
						?locationCreated owl:sameAs ?locationCreatedSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:dateCreated ?dateCreated .
				}
			}
			UNION {
				?creativeWork a schema:Sculpture;
				schema:creator ?uri ;
				schema:name ?name .
				OPTIONAL {
					?creativeWork dbo:genre ?genre .
					?genre rdfs:label ?genreLabel .
					OPTIONAL {
						?genre owl:sameAs ?genreSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:locationCreated ?locationCreated .
					?locationCreated rdfs:label ?locationCreatedLabel .
					OPTIONAL {
						?locationCreated owl:sameAs ?locationCreatedSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:dateCreated ?dateCreated .
				}
			}
			BIND (URI(REPLACE(STR(?genre), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?genreURI)
		} ORDER BY ASC(?dateCreated)
	""")
	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		work = CreativeWork(result["creativeWork"]["value"])
		work.work = result["creativeWork"]["value"]
		work.name = result["name"]["value"]
		work.genreURI = result["genreURI"]["value"] if ("genreURI" in result) else None
		work.genre = result["genreLabel"]["value"] if ("genre" in result) else None
		work.genreSameAs = result["genreSameAs"]["value"] if ("genreSameAs" in result) else None
		work.publisher = result["publisherLabel"]["value"] if ("publisher" in result) else None
		work.publisherSameAs = result["publisherSameAs"]["value"] if ("publisherSameAs" in result) else None
		work.locationCreated = result["locationCreatedLabel"]["value"] if ("locationCreated" in result) else None
		work.locationCreatedSameAs = result["locationCreatedSameAs"]["value"] if ("locationCreatedSameAs" in result) else None
		work.dateCreated = result["dateCreated"]["value"] if ("dateCreated" in result) else None
		works.append(work)

	actions = []
	# query to get actions
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		PREFIX dct: <http://purl.org/dc/terms/>
		PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
		SELECT DISTINCT * WHERE {
			VALUES ?uri{
				<"""+uri+""">
		    	# Other values go here
			}
			{
				?action a schema:Action;
				schema:agent ?uri ;
				schema:name ?name .
				OPTIONAL {
					?action schema:location ?location .
					?location rdfs:label ?locationLabel .
					OPTIONAL {
					?location owl:sameAs ?locationSameAs .
					}
				}
				OPTIONAL {
					?action schema:startTime ?startTime .
				}
				OPTIONAL {
					?action dct:subject ?concept .
					?concept skos:prefLabel ?conceptLabel .
				}
			}
			BIND (URI(REPLACE(STR(?action), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?actionURI)
			BIND (URI(REPLACE(STR(?concept), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?conceptURI)
		} ORDER BY ASC(?startTime)
	""")
	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		action = Action(result["name"]["value"])
		action.URI = result["actionURI"]["value"]
		action.name = result["name"]["value"]
		action.location = result["locationLabel"]["value"] if ("location" in result) else None
		action.locationSameAs = result["locationSameAs"]["value"] if ("locationSameAs" in result) else None
		action.startTime = result["startTime"]["value"] if ("startTime" in result) else None
		action.conceptURI = result["conceptURI"]["value"] if ("conceptURI" in result) else None
		action.concept = result["conceptLabel"]["value"] if ("conceptLabel" in result) else None
		actions.append(action)

	academicEducations = []
	# query to get Academic Education
	sparql.setQuery("""
		PREFIX ipers: <http://data.utpl.edu.ec/ipers/vocabulary/>
		SELECT DISTINCT * WHERE {
			<"""+uri+"""> ipers:hasStage ?academicEducationStage .
			?academicEducationStage a ipers:AcademicEducationStage ;
			ipers:institution ?institution .
			?institution rdfs:label ?institutionLabel .
			OPTIONAL {
				?institution owl:sameAs ?institutionSameAs .
				}
			OPTIONAL {
				?academicEducationStage ipers:studyField ?studyField .
			}
			OPTIONAL {
				?academicEducationStage ipers:place ?place .
				?place rdfs:label ?placeLabel .
				OPTIONAL {
					?place owl:sameAs ?placeSameAs .
				}
			}
			OPTIONAL {
				?academicEducationStage ipers:startDate ?startDate .
			}
			OPTIONAL {
				?academicEducationStage ipers:endDate ?endDate .
			}
			BIND (URI(REPLACE(STR(?institution), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?institutionURI)
		}
		ORDER BY ASC(?startDate)	
	""")
	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		academicEducation = AcademicEducation(result["institution"]["value"])
		academicEducation.institutionURI = result["institutionURI"]["value"]
		academicEducation.institution = result["institutionLabel"]["value"]
		academicEducation.institutionSameAs = result["institutionSameAs"]["value"] if ("institutionSameAs" in result) else None
		academicEducation.studyField = result["studyField"]["value"] if ("studyField" in result) else None
		academicEducation.place = result["placeLabel"]["value"] if ("place" in result) else None
		academicEducation.placeSameAs = result["placeSameAs"]["value"] if ("placeSameAs" in result) else None
		academicEducation.startDate = result["startDate"]["value"] if ("startDate" in result) else None
		academicEducation.endDate = result["endDate"]["value"] if ("endDate" in result) else None
		academicEducations.append(academicEducation)

	awards = []
	# query to get awards
	sparql.setQuery("""
		PREFIX ipers: <http://data.utpl.edu.ec/ipers/vocabulary/>
		SELECT DISTINCT * WHERE {
			<"""+uri+"""> ipers:hasMoment ?awardMoment .
			?awardMoment a ipers:AwardMoment ;
			ipers:award ?award .
			?award rdfs:label ?awardName .
			OPTIONAL {
				?award owl:sameAs ?awardSameAs .
			}
			OPTIONAL {
				?awardMoment ipers:cause ?awardCause .
			}
			OPTIONAL {
				?awardMoment ipers:event ?awardEvent .
				?awardEvent rdfs:label ?awardEventLabel .
			}
			OPTIONAL {
				?awardMoment ipers:conferredBy ?conferredBy .
				?conferredBy rdfs:label ?conferredByLabel .
				OPTIONAL {
					?conferredBy owl:sameAs ?conferredBySameAs .
				}
			}
			OPTIONAL {
				?awardMoment ipers:date ?date .
			}
			OPTIONAL {
				?awardMoment ipers:conferredIn ?conferredIn .
				?conferredIn rdfs:label ?awardPlace .
				OPTIONAL {
					?conferredIn owl:sameAs ?awardPlaceSameAs .
				}
			}
			BIND (URI(REPLACE(STR(?award), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?awardURI)
			BIND (URI(REPLACE(STR(?awardEvent), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?awardEventURI)
			BIND (URI(REPLACE(STR(?conferredBy), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?conferredByURI)
		} ORDER BY ASC(?date)
	""")
	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		award = Award(result["awardName"]["value"])
		award.URI = result["awardURI"]["value"]
		award.name = result["awardName"]["value"]
		award.sameAs = result["awardSameAs"]["value"] if ("awardSameAs" in result) else None
		award.cause = result["awardCause"]["value"] if ("awardCause" in result) else None
		award.eventURI = result["awardEventURI"]["value"] if ("awardEventURI" in result) else None
		award.event = result["awardEventLabel"]["value"] if ("awardEventLabel" in result) else None
		award.conferredByURI = result["conferredByURI"]["value"] if ("conferredByURI" in result) else None
		award.conferredBy = result["conferredByLabel"]["value"] if ("conferredBy" in result) else None
		award.conferredBySameAs = result["conferredBySameAs"]["value"] if ("conferredBySameAs" in result) else None
		award.date = result["date"]["value"] if ("date" in result) else None
		award.conferredIn = result["awardPlace"]["value"] if ("conferredIn" in result) else None
		award.conferredInSameAs = result["awardPlaceSameAs"]["value"] if ("awardPlaceSameAs" in result) else None
		awards.append(award)

	bibliographicReferences = []
	# query to get awards
	sparql.setQuery("""
		PREFIX ipers: <http://data.utpl.edu.ec/ipers/vocabulary/>
		PREFIX dct: <http://purl.org/dc/terms/>
		PREFIX dbo: <http://dbpedia.org/ontology/>

		SELECT ?bibliographicResourceLabel (group_concat(?creatorLabel;separator=", ") as ?allCreators) ?created ?publisherLabel ?source ?libraryLabel ?libraryPlaceLabel WHERE {
			<"""+uri+"""> ipers:informationSource ?bibliographicResource .
			?bibliographicResource rdfs:label ?bibliographicResourceLabel .
			OPTIONAL {
				?bibliographicResource dct:creator ?creator .
				?creator rdfs:label ?creatorLabel .
			}
			OPTIONAL {
				?bibliographicResource dct:created ?created .
			}
			OPTIONAL {
				?bibliographicResource dct:publisher ?publisher .
				?publisher rdfs:label ?publisherLabel .
			}
			OPTIONAL {
				<"""+uri+"""> foaf:firstName ?name . 
				?bibliographicResource dct:source ?source .
				FILTER (regex(?source, ?name, "i"))
			}
			OPTIONAL {
				?bibliographicResource ipers:availableIn ?library .
				?library rdfs:label ?libraryLabel ;
				dbo:location ?libraryPlace .
				?libraryPlace rdfs:label ?libraryPlaceLabel .
			}
		}
	""")
	sparql.setReturnFormat(JSON)
	resultss = sparql.query().convert()

	for result in resultss["results"]["bindings"]:
		bibliographicReference = BibliographicReference(result["bibliographicResourceLabel"]["value"])
		bibliographicReference.name = result["bibliographicResourceLabel"]["value"]
		bibliographicReference.creator = result["allCreators"]["value"] if ("allCreators" in result) else None
		bibliographicReference.date = result["created"]["value"] if ("created" in result) else None
		bibliographicReference.publisher = result["publisherLabel"]["value"] if ("publisher" in result) else None
		bibliographicReference.source = result["source"]["value"] if ("source" in result) else None
		bibliographicReference.library = result["libraryLabel"]["value"] if ("libraryLabel" in result) else None
		bibliographicReference.libraryPlace = result["libraryPlaceLabel"]["value"] if ("libraryPlaceLabel" in result) else None
		bibliographicReferences.append(bibliographicReference)

	return render(request, 'person.html', {
		'person':person, 
		'images':images, 
		'externalURIs':externalURIs, 
		'nationalities':nationalities,
		'residences':residences,
		'knownFors':knownFors,
		'occupations':occupations,
		'parents':parents, 
		'siblings':siblings, 
		'spouses':spouses, 
		'children':children, 
		'professions':professions, 
		'jobs':jobs, 
		'works':works, 
		'actions':actions, 
		'academicEducations':academicEducations, 
		'awards':awards,
		'bibliographicReferences':bibliographicReferences,
		'concepts':concepts
		})


# Vista para búsqueda de personajes
def search_result(request):
	search = request.GET.get('search')
	print(search)
	# search.encode('utf-8')
	# search.decode('latin-1')
	# search.decode('utf-8')
	print(search)
	sparql = SPARQLWrapper("http://ld.utpl.edu.ec/sparql")
	sparql.setQuery("""
		SELECT ?person ?firstName ?lastName (SAMPLE(?image) AS ?image) WHERE {
		{
			?person rdf:type foaf:Person ;
			foaf:firstName ?firstName;
			foaf:lastName ?lastName .
			BIND(concat(?firstName," ",?lastName) AS ?fullName)
			FILTER (regex(?fullName, '"""+search+"""', "i") || regex(str(?person), '"""+search+"""', "i"))
		}
		OPTIONAL {
			?person foaf:img ?image .
		}
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	# Array that contains the illustrious people
	people = []

	for result in results["results"]["bindings"]:
		person = Person(result["firstName"]["value"])
		person.uri = result["person"]["value"]
		person.firstName = result["firstName"]["value"]
		person.lastName = result["lastName"]["value"]
		person.image = result["image"]["value"] if ("image" in result) else None
		people.append(person)
	return render(request, 'search_result.html', {
		'people':people,
		'search':search
		})


def works(request):
	sparql = SPARQLWrapper("http://ld.utpl.edu.ec/sparql")
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		SELECT DISTINCT * WHERE {
			{
				?creativeWork a schema:CreativeWork;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:MusicComposition;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Book;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Painting;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Sculpture;
				schema:name ?name .
			}
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	# Array that contains the works
	works = []

	for result in results["results"]["bindings"]:
		work = CreativeWork(result["creativeWork"]["value"])
		work.uri = result["creativeWork"]["value"]
		work.name = result["name"]["value"]
		works.append(work)

	paginator = Paginator(works, 8) # Show 8 works per page
	page = request.GET.get('page')
	try:
	    works = paginator.page(page)
	except PageNotAnInteger:
        # If page is not an integer, deliver first page.
	    works = paginator.page(1)
	except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
	    works = paginator.page(paginator.num_pages)

	return render(request, 'works.html', {'works':works})

def work(request):
	uri = request.GET.get('uri')
	sparql = SPARQLWrapper("http://ld.utpl.edu.ec/sparql")
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		PREFIX dbo: <http://dbpedia.org/ontology/>
		SELECT DISTINCT * WHERE {
			VALUES ?creativeWork{
				<"""+uri+""">
			}
			{
				?creativeWork schema:name ?name .
				OPTIONAL {
					?creativeWork dbo:genre ?genre .
					?genre rdfs:label ?genreLabel .
					OPTIONAL {
						?genre owl:sameAs ?genreSameAs .
					}
				}
				OPTIONAL {
					?creativeWork schema:dateCreated ?dateCreated .
				}
				OPTIONAL {
					?creativeWork schema:creator ?creator .
					?creator rdfs:label ?creatorLabel .
				}
				OPTIONAL {
					?creativeWork schema:composer ?composer .
					?composer rdfs:label ?composerLabel .
				}
				OPTIONAL {
					?creativeWork schema:lyricist ?lyricist .
					?lyricist rdfs:label ?lyricistLabel .
				}
			}
			BIND (URI(REPLACE(STR(?creativeWork), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?creativeWorkURI)
			BIND (URI(REPLACE(STR(?genre), "http://data.utpl.edu.ec/", "http://localhost:8080/")) AS ?genreURI)
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	for result in results["results"]["bindings"]:
		work = CreativeWork(result["creativeWork"]["value"])
		work.work = result["creativeWorkURI"]["value"]
		work.name = result["name"]["value"]
		work.genreURI = result["genreURI"]["value"] if ("genreURI" in result) else None
		work.genre = result["genreLabel"]["value"] if ("genre" in result) else None
		work.genreSameAs = result["genreSameAs"]["value"] if ("genreSameAs" in result) else None
		work.dateCreated = result["dateCreated"]["value"] if ("dateCreated" in result) else None
		work.creatorURI = result["creator"]["value"] if ("creator" in result) else None
		work.creator = result["creatorLabel"]["value"] if ("creator" in result) else None
		work.composerURI = result["composer"]["value"] if ("composer" in result) else None
		work.composer = result["composerLabel"]["value"] if ("composer" in result) else None
		work.lyricistURI = result["lyricist"]["value"] if ("lyricist" in result) else None
		work.lyricist = result["lyricistLabel"]["value"] if ("lyricist" in result) else None
		
	return render(request, 'work.html', {'work':work})

# Vista para búsqueda de obras
def work_search_result(request):
	search = request.GET.get('search').lower()
	sparql = SPARQLWrapper("http://ld.utpl.edu.ec/sparql")
	sparql.setQuery("""
		PREFIX schema: <http://schema.org/>
		SELECT DISTINCT * WHERE {
			{
				?creativeWork a schema:CreativeWork;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:MusicComposition;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Book;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Painting;
				schema:name ?name .
			}
			UNION {
				?creativeWork a schema:Sculpture;
				schema:name ?name .
			}
			FILTER regex(lcase(?name), '"""+search+"""')
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	# Array that contains the works
	works = []

	for result in results["results"]["bindings"]:
		work = CreativeWork(result["creativeWork"]["value"])
		work.uri = result["creativeWork"]["value"]
		work.name = result["name"]["value"]
		works.append(work)
	return render(request, 'work_search_result.html', {'works':works})
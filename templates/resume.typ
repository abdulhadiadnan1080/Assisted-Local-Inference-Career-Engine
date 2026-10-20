#let data = json("resume.json")

#set document(title: data.name, author: data.name)
#set page(paper: "us-letter", margin: 18mm)
#set text(font: "New Computer Modern", size: 11pt, fill: rgb("181818"))
#set par(leading: 0.55em)
#set list(indent: 1.15em, body-indent: 0.42em, spacing: 0.34em, marker: [•])

#align(center)[
  #text(size: 21pt, weight: "bold", data.at("name", default: "Operator"))
  #v(0.3em)
  #text(size: 11pt, data.at("headline", default: ""))
  #v(0.2em)
  #text(size: 10pt, fill: rgb("444444"), data.at("email", default: "") + "  ·  " + data.at("location", default: ""))
]

#v(0.4em)
#text(size: 12pt, weight: "bold", upper("Summary"))
#line(length: 100%, stroke: 0.6pt + rgb("444444"))
#data.at("summary", default: "")

#v(0.5em)
#text(size: 12pt, weight: "bold", upper("Technical Skills"))
#line(length: 100%, stroke: 0.6pt + rgb("444444"))
#data.at("skills", default: ()).join(", ")

#v(0.5em)
#text(size: 12pt, weight: "bold", upper("Experience"))
#line(length: 100%, stroke: 0.6pt + rgb("444444"))

#for job in data.at("experience", default: ()) [
  #strong(job.at("company", default: ""))
  #linebreak()
  #text(size: 10.8pt, job.at("role", default: "") + " | " + job.at("dates", default: ""))
  #if job.at("location", default: "") != "" [
    #text(size: 10.8pt, fill: rgb("555555"), " - " + job.at("location"))
  ]
  #v(0.12em)
  #list(..job.at("bullets", default: ()))
  #v(0.34em)
]

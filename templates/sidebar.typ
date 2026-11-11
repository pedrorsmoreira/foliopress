#let p = json(sys.inputs.at("profile"))
#let settings = json(sys.inputs.at("settings"))
#let omitted = settings.omitted_experience
#let accent = rgb("234b61")
#let muted = rgb("505b63")
#set document(title: p.name + " — CV", author: p.name)
#set page(paper: "a4", margin: (x: 11mm, y: 12mm), background: place(top + left, rect(width: 59mm, height: 100%, fill: accent, stroke: none)))
#set text(font: "Liberation Sans", size: 10.5pt, lang: "en", ligatures: false)
#set par(leading: 0.35em, spacing: 0.4em)
#show link: set text(fill: accent)
#let section(title) = [
  #v(9pt, weak: false)
  #block(sticky: true)[
    #text(size: 10pt, weight: "bold", fill: accent, tracking: 0.8pt)[#upper(title)]
    #v(2pt)
    #line(length: 100%, stroke: 0.5pt + accent)
  ]
  #v(4pt, weak: false)
]
#let labeldate(left, right) = grid(columns: (1fr, auto), column-gutter: 10pt, left, text(size: 9pt, fill: muted, right))
#place(top + left, dx: 55mm)[#block(width: 133mm)[
  #text(size: 26pt, weight: "bold", fill: accent, p.name)
  #v(5pt, weak: false)
  #text(size: 12pt, p.title)
#section("Experience")
#let visible-jobs = p.experience.filter(job => job.at("id", default: "") not in omitted)
#let spacing = (role-content: 8pt, topic: 9pt, heading-body: 3pt, contribution: 5pt, employer: 15pt)
#for (job-index, job) in visible-jobs.enumerate() {
  if job-index > 0 { v(spacing.employer, weak: false) }
  block(sticky: true)[
    #labeldate([#text(weight: "bold", size: 14pt, fill: accent, job.company)], job.dates)
    #v(2pt, weak: false)
    #text(size: 9.5pt)[#job.role · #text(fill: muted, job.location)]
  ]
  // Every job has the same lead-in, even when its first contribution has no heading.
  v(spacing.role-content, weak: false)
  let topics = ()
  for group in job.groups {
    if group.heading == "Main Contributions" {
      for bullet in group.bullets {
        let pieces = bullet.split(": ")
        topics.push((heading: if pieces.len() > 1 { pieces.first() } else { "" },
          bullets: (pieces.slice(if pieces.len() > 1 { 1 } else { 0 }).join(": "),)))
      }
    } else { topics.push(group) }
  }
  for (topic-index, topic) in topics.enumerate() {
    if topic-index > 0 { v(spacing.topic, weak: false) }
    if topic.heading != "" {
      block(sticky: true, strong(topic.heading))
      v(spacing.heading-body, weak: false)
    }
    for (bullet-index, bullet) in topic.bullets.enumerate() {
      if bullet-index > 0 { v(spacing.contribution, weak: false) }
      if topic.bullets.len() > 1 {
        block(list(indent: 0pt, body-indent: 10pt, [#bullet]))
      } else { block(bullet) }
    }
  }
}
]]
#block(width: 42mm)[
  #set text(size: 9.5pt, fill: white)
  #set par(leading: 0.45em)
  #show link: set text(fill: white)
  #let sideheading(title) = [
    #text(size: 11pt, weight: "bold", tracking: 0.8pt)[#upper(title)]
    #v(5pt, weak: false)
    #line(length: 100%, stroke: 0.5pt + rgb("a7becb"))
    #v(5pt, weak: false)
  ]
  #sideheading("Contact")
  #text(weight: "bold")[Location]
  #parbreak()
  #p.location
  #v(5pt, weak: false)
  #text(weight: "bold")[Phone]
  #parbreak()
  #p.phone
  #v(5pt, weak: false)
  #text(weight: "bold")[Email]
  #parbreak()
  #link("mailto:" + p.email, p.email)
  #v(5pt, weak: false)
  #text(weight: "bold")[LinkedIn]
  #parbreak()
  #link(p.linkedin, p.linkedin.split("/").filter(s => s != "").last())
  #v(5pt, weak: false)
  #text(weight: "bold")[GitHub]
  #parbreak()
  #link(p.github, p.github.split("/").filter(s => s != "").last())
  #v(18pt, weak: false)
  #sideheading("Skills")
  #for skill in p.skills {
    block(text(weight: "bold", size: 10.5pt, skill.heading))
    v(7pt, weak: false)
    for item in skill.items {
      block(item)
      v(4pt, weak: false)
    }
    v(9pt, weak: false)
  }
  #v(5pt, weak: false)
  #sideheading("Languages")
  #for language in p.languages.split(" · ") {
    block(language)
    v(5pt, weak: false)
  }
  #v(14pt, weak: false)
  #sideheading("Education")
  #set text(size: 9pt)
  #for edu in p.education {
    block(breakable: false)[
      #strong(edu.school)
      #v(3pt, weak: false)
      #edu.location
      #v(3pt, weak: false)
      #edu.dates
      #v(4pt, weak: false)
      #edu.degree
      #v(4pt, weak: false)
      #edu.detail
    ]
    v(9pt, weak: false)
  }
]

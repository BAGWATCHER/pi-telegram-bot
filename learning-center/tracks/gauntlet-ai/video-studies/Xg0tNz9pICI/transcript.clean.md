# Transcript (cleaned)

- Video ID: Xg0tNz9pICI
- Lines: 3998

[00:00:00] dark factory today. And I know it sounds
[00:00:02] kind of spooky, but I'll start things
[00:00:04] off by explaining what that actually is.
[00:00:06] This is going to be a little bit more of
[00:00:08] a casual live stream. So, I did a live
[00:00:10] stream over the weekend where I dove
[00:00:12] really deep into Archon, the new
[00:00:15] open-source harness builder.
[00:00:18] And so, I'm going to be actually be
[00:00:20] using this a lot today, but I want to
[00:00:23] just do more like a live building
[00:00:24] session. So, I'll still like be sure to
[00:00:26] explain everything that I'm doing and
[00:00:28] have a good time for Q&A and stuff, but
[00:00:31] it's going to be a little bit more like
[00:00:32] you guys just get to see the inside of a
[00:00:34] process that I'm starting here with a
[00:00:37] public experiment that I'm calling the
[00:00:39] dark factory.
[00:00:41] And so, I've got my left monitor open up
[00:00:43] here with all of your guys' comments in
[00:00:46] the chat, and then my right monitor
[00:00:49] where I have my recording software, and
[00:00:51] then I've got my screen in the middle
[00:00:52] here. So, when you see me looking
[00:00:53] around, that's what I'm doing.
[00:00:55] But yeah, this is just going to be like
[00:00:56] a a good like two two and a half hours
[00:00:59] I'm thinking of streaming for where I'm
[00:01:00] going to be building the dark factory in
[00:01:02] public with you guys, and even opening
[00:01:05] this up fully to the public in a couple
[00:01:07] weeks here. I'll talk about that means
[00:01:08] as well, but I I need to explain first
[00:01:11] what the heck a dark factory actually
[00:01:13] is. So, I'll I'll cover the basics for
[00:01:16] you guys. I think you'll find it really
[00:01:17] really interesting.
[00:01:19] Because this is like the peak evolution
[00:01:21] of AI coding. Not that a dark factory is
[00:01:24] going to give you the most reliable
[00:01:26] results, but it is the way to get the
[00:01:27] most control possible to your AI coding
[00:01:31] assistants when they're working on a
[00:01:32] code base. So, the idea of the dark
[00:01:35] factory, it originated actually in the
[00:01:38] late I think like 1980s, 1990s. There
[00:01:41] were some companies in China that were
[00:01:44] running physical production lines with
[00:01:47] only robots. And so, the physical
[00:01:49] location only had robots in it, so they
[00:01:52] didn't even have to have the lights on,
[00:01:54] right? There's no need to pay for
[00:01:55] electricity when there's no humans
[00:01:57] operating in the facility.
[00:01:59] And so, Dan Shapiro, I believe he's the
[00:02:01] first one that took [clears throat] this
[00:02:03] idea of the dark factory and applied it
[00:02:06] to code bases. So, using generative AI
[00:02:09] to completely manage a code base all the
[00:02:12] way from ideation, implementation, code
[00:02:15] review, merging pull requests, handling
[00:02:17] releases, like actually shipping the
[00:02:19] code as well. That is what a dark
[00:02:20] factory is. And I think the best way to
[00:02:23] explain it is to go through his article
[00:02:25] here.
[00:02:26] So, he put this out just at the end of
[00:02:27] January this year. And he talks about
[00:02:30] the five levels of AI coding. A lot of
[00:02:33] us are at level like three or four right
[00:02:35] now. So, I I think like seeing where
[00:02:37] you're at and then like how far we can
[00:02:39] take things with the dark factory with
[00:02:40] his analogy will
[00:02:43] like really help you understand like
[00:02:45] exactly what the heck a dark factory is.
[00:02:48] And so, yeah, let me go and share my
[00:02:51] screen here with this blog article. I
[00:02:54] actually meant to be sharing my screen
[00:02:55] earlier, so that's my bad, but yeah, so
[00:02:59] let's take a look at this together here.
[00:03:00] So, this is Dan Shapiro's post
[00:03:02] So, the five levels from spicy auto
[00:03:05] complete to the dark factory.
[00:03:09] And so, level zero, this is how I
[00:03:12] started using AI to help me code.
[00:03:14] Probably the same for a lot of you guys
[00:03:16] that came from an engineering
[00:03:17] background. You were writing code
[00:03:19] yourself before, and then you slowly
[00:03:22] start leaning on AI more and more. So, I
[00:03:24] don't know why he calls it spicy auto
[00:03:26] complete, but hey, I love it, so I'm I'm
[00:03:29] for it. So, and in this [snorts] case,
[00:03:32] the analogy that he uses throughout the
[00:03:33] different levels is our control of a
[00:03:36] vehicle.
[00:03:37] So, at level zero, we're still driving.
[00:03:40] You can even think of it as like stick
[00:03:41] shift, right? Like super manual. We are
[00:03:44] managing the vehicle. And so, the AI
[00:03:47] coding assistant or even just like the
[00:03:49] large language model serves as a
[00:03:51] reference tool or an enhanced search.
[00:03:53] So, it's like a smarter stack overflow
[00:03:55] if you guys have used stack overflow in
[00:03:57] the past. And so, here the developer
[00:04:00] manually writes all the code. We're just
[00:04:02] using AI as an advisor. So, like help me
[00:04:04] with this code snippet or give me an
[00:04:06] idea for how I can implement this, but
[00:04:08] we still are the ones hands on the
[00:04:10] keyboard writing the actual code.
[00:04:12] So, hopefully most of us aren't at this
[00:04:15] step anymore. Um I know some people
[00:04:17] still are cuz that's what what they're
[00:04:18] comfortable with, and that's totally
[00:04:20] okay. Uh but then we go into level one.
[00:04:22] This is the coding intern. So, you can
[00:04:25] think of it like cruise control. You
[00:04:26] still have your hands on the wheel, but
[00:04:28] at least AI is managing something or
[00:04:30] like the car is managing keeping you at
[00:04:32] a certain speed like 65 mph. So, here
[00:04:36] the AI writes the unimportant or
[00:04:38] boilerplate code. So, you're still doing
[00:04:41] most of the work yourself, but for the
[00:04:42] things that you don't require much trust
[00:04:44] in the large language model, you're
[00:04:45] starting to hand it over.
[00:04:47] That's the coding intern.
[00:04:49] And by the way, when we get to level
[00:04:51] five, I'll talk about how I'm actually
[00:04:53] building it myself. So, we'll we'll get
[00:04:54] there, but I want to kind of give the
[00:04:56] basis for you here. So, we then get to
[00:04:58] level two, the junior developer. This is
[00:05:00] the pair programmer. So, we start to
[00:05:02] relax a little bit. We only have one
[00:05:04] hand on the wheel instead of two. So,
[00:05:06] the developer and AI trade off control.
[00:05:08] So, there are legitimately some more
[00:05:10] complex tasks that we are delegating to
[00:05:12] the coding agent, but not all of the
[00:05:13] time. We still are the ones writing the
[00:05:16] code a lot.
[00:05:18] And then we get to level three. And so,
[00:05:20] this is, you know, like the self-driving
[00:05:22] cars now, right? Like you got hands off
[00:05:23] the wheel, but you're still paying
[00:05:25] attention to the road. And so, the AI is
[00:05:28] generating a majority of the code base,
[00:05:30] but you're still reviewing everything
[00:05:32] that the AI does. Like you're watching
[00:05:34] the road constantly, and you're going to
[00:05:36] be nitpicky. You're going to review
[00:05:38] plans, you're going to give feedback,
[00:05:39] you're going to review the code like the
[00:05:40] pull requests before you merge it.
[00:05:42] You're always the bottleneck for
[00:05:44] verification before progressing. That's
[00:05:46] level three. And honestly, that's where
[00:05:49] most of us are. And you know, like when
[00:05:52] I teach AI coding on my channel and in
[00:05:54] the Dynamis community,
[00:05:56] level three is actually what I generally
[00:05:58] recommend. Because this is the furthest
[00:06:00] you can push it right now and still get
[00:06:03] the most reliable results possible. So,
[00:06:06] at level four,
[00:06:08] um this is where we get into the
[00:06:09] engineering team. When we get into
[00:06:10] harnesses for longer running tasks. And
[00:06:13] so, this is where you actually get to
[00:06:14] fall asleep at the wheel. So, you let
[00:06:17] the AI run unattended for long periods
[00:06:19] handling very complex tasks. And so, you
[00:06:21] think of harnesses like the Rel loop or
[00:06:24] Anthropic's harness giving your second
[00:06:25] brain the ability to handle issues and
[00:06:28] pull requests end to end. So, here you
[00:06:31] still are going to check the final
[00:06:32] results. Like at some point, you're
[00:06:33] going to you're going to wake up and
[00:06:34] just like make sure the car is actually
[00:06:36] driving you to the right place, and you
[00:06:38] know, take your put your hands on the
[00:06:39] wheel if you need to, but for the most
[00:06:42] part, you're trusting the coding agent
[00:06:43] to handle insanely long sets of work.
[00:06:47] So, level four, I I wouldn't say this is
[00:06:49] like the most reliable at this point. If
[00:06:50] you want to ship the most reliable
[00:06:52] production code possible, you're still
[00:06:54] at level three. Cuz you're still going
[00:06:55] to monitor everything and be the
[00:06:57] bottleneck for verification, but you're
[00:06:58] starting to really take yourself out of
[00:07:00] the loop with level four,
[00:07:02] but there's still the steering wheel,
[00:07:04] right? Like there's still the
[00:07:05] opportunity for you to step in and fix
[00:07:07] things yourself or steer the agents in a
[00:07:10] different direction in the middle of
[00:07:12] some implementation.
[00:07:14] And then that brings us into level five.
[00:07:17] And I love the car analogy here cuz you
[00:07:19] like you look at level four, and there's
[00:07:21] still the steering wheel, like right?
[00:07:22] There's still the opportunity for you to
[00:07:24] have control, but in level five, your
[00:07:26] vehicle looks like this, which someday
[00:07:28] we'll get there. That'll that'll be
[00:07:29] really cool. The day that I have a
[00:07:31] vehicle looks like this. But there's no
[00:07:33] there's no steering wheel in this
[00:07:35] vehicle. There's not even the option for
[00:07:37] us to take the reins if we want. That's
[00:07:40] what a dark factory is.
[00:07:42] So, the engineer manages the goal in the
[00:07:44] system, right? There's still some kind
[00:07:46] of console here to provide higher level
[00:07:48] direction. We're still going to write
[00:07:49] the PRDs. We might manage the some of
[00:07:52] the releases, but we're not managing the
[00:07:55] code. So, we provide plain English
[00:07:57] descriptions, but the agent defines
[00:07:58] implementation, writes code, tests,
[00:08:01] fixes bugs, and ships. That is a dark
[00:08:04] factory.
[00:08:05] And that my friend is what we are going
[00:08:08] to be building today. I have a good
[00:08:10] amount of the system already set up
[00:08:12] because I don't want to go through all
[00:08:13] the like really boring parts with you,
[00:08:15] but I I want to work on the workflows
[00:08:19] today. Like actually build the workflows
[00:08:21] that are going to manage the entire dark
[00:08:23] factory.
[00:08:24] Because it's not enough to just point
[00:08:26] Claude code at a GitHub repo and say
[00:08:29] manage everything. Right? We have to
[00:08:30] teach it like how do we want it to
[00:08:32] handle issues? What kinds of features
[00:08:34] are we going to build into this
[00:08:36] application? How do we want to evolve
[00:08:38] it? What are the constraints that we
[00:08:40] have? How are we going to review code,
[00:08:43] right? Like we have to create workflows
[00:08:44] to define exactly how we want to write.
[00:08:47] So, right? So, like the engineer manages
[00:08:49] the goal in the system. I'm talking
[00:08:50] about building the system here for this
[00:08:53] vehicle.
[00:08:54] And so,
[00:08:55] um what I'm going to be doing, and this
[00:08:57] is this is the most exciting part for
[00:08:59] me,
[00:09:00] is I'm going to be leveraging Archon
[00:09:02] workflows to manage every single part of
[00:09:05] the dark factory. So, Archon is my first
[00:09:08] ever or it is the first ever open-source
[00:09:11] harness for AI coding. First ever
[00:09:13] harness builder, sorry. So, you think
[00:09:16] about like whatever your process is
[00:09:18] right now for software development,
[00:09:19] however you work with AI coding
[00:09:21] assistants, Archon allows you to build
[00:09:23] workflows to package everything up so
[00:09:25] that you can build any on any code base.
[00:09:28] You can invoke any workflow.
[00:09:30] >> [clears throat]
[00:09:30] >> Excuse me. You can invoke any workflow
[00:09:32] in parallel, and you get reliable
[00:09:34] results every single time because you're
[00:09:36] taking your process and you're packaging
[00:09:38] it up. That's what Archon gives us. And
[00:09:40] so, if you're interested more how Archon
[00:09:42] works and you haven't seen my content on
[00:09:44] it recently, there's a lot that I put
[00:09:46] out on my channel recently. So, there's
[00:09:48] a couple of live streams that I did,
[00:09:49] actually one just two days ago. Um so, I
[00:09:51] did it just on Saturday last week.
[00:09:55] And then I also have a YouTube video. My
[00:09:57] most recent YouTube video where I
[00:09:58] covered Archon. So, I'm not going to get
[00:10:00] like super deep into an introduction to
[00:10:02] Archon today because I already have this
[00:10:04] content, but I'm going to be using it as
[00:10:06] a very critical part of the workflow, of
[00:10:09] the whole system for the Dark Factory
[00:10:11] because it's going to drive everything.
[00:10:13] I'm going to build Archon workflows to
[00:10:16] manage my issues, build Archon workflows
[00:10:18] to write the code, review the code,
[00:10:22] manage the releases. I'll talk about
[00:10:24] what that looks like when I get into my
[00:10:26] plan here. So, I have this entire
[00:10:29] markdown document
[00:10:31] that outlines my entire plan for the
[00:10:34] Dark Factory. And I took a lot of
[00:10:36] inspiration from
[00:10:38] you know other examples of Dark
[00:10:40] Factories that are already out there on
[00:10:41] the internet. And so, maybe you guys
[00:10:43] have heard of the Strong DM use case.
[00:10:47] So, Strong DM is a company that they
[00:10:50] actually manage a production codebase
[00:10:53] with a Dark Factory. They are shipping
[00:10:55] pull requests all of the time that don't
[00:10:58] have any human review at all. And their
[00:11:01] Dark Factory is unfortunately not open
[00:11:03] source like mine is going to be for you
[00:11:05] guys to see and watch it evolve in real
[00:11:07] time.
[00:11:09] But they did share something like a PRD.
[00:11:12] So, they have this open source spec for
[00:11:16] building their Dark Factory. They call
[00:11:18] it the Attractor.
[00:11:20] And so, we don't have the codebase, but
[00:11:21] we do have the plan document that I
[00:11:24] guess theoretically you can use to have
[00:11:26] your coding agent build out exactly what
[00:11:28] they have for managing their codebase
[00:11:31] with no humans involved. And so, I did
[00:11:33] actually take a lot of inspiration from
[00:11:35] the ideas here. If you guys are
[00:11:37] interested in any of this, I'm planning
[00:11:39] on putting out a YouTube video tomorrow
[00:11:41] where I'll have like a more concise
[00:11:42] overview of everything and I'll have
[00:11:44] links to this all.
[00:11:45] I can of course put links to this in the
[00:11:47] chat too if you guys are curious. So,
[00:11:50] um I will
[00:11:52] put a link to this blog post right here.
[00:11:57] And then
[00:11:58] um I'll put a link to this resource
[00:12:01] covering the
[00:12:02] Dark the Strong DM Dark Factory. If you
[00:12:04] guys want to read through it.
[00:12:07] Just want to make sure I give those
[00:12:08] to you guys cuz that's a lot of like my
[00:12:10] initial research for building a Dark
[00:12:12] Factory.
[00:12:13] And I'm super fascinated by this. So,
[00:12:17] okay, let me be really clear here. I
[00:12:18] want to uh we clear on something and
[00:12:20] then I'll explain more of that the
[00:12:21] architecture that I have for my Archon
[00:12:24] Dark Factory.
[00:12:26] I know I already said this, but it's
[00:12:28] worth repeating. The you're not going to
[00:12:29] get the most reliable results with your
[00:12:31] coding agent when you give it this much
[00:12:34] autonomy. I highly recommend when you're
[00:12:36] doing things for real, you put yourself
[00:12:39] in the loop, at least reviewing plans
[00:12:41] and reviewing code. Those two stages of
[00:12:45] the development cycle, I would at least
[00:12:47] have those.
[00:12:48] So, this is definitely a public
[00:12:50] experiment. I'm calling it an experiment
[00:12:52] because it might fall completely flat on
[00:12:55] its face. We'll see. I mean, I'm going
[00:12:57] to put a lot of work into trying to make
[00:12:58] it really reliable, but
[00:13:01] I have no idea how the codebase is going
[00:13:03] to end up evolving when I leave it to
[00:13:05] literally manage itself. And so, the
[00:13:08] input for the Dark Factory is going to
[00:13:10] be a GitHub issue.
[00:13:12] So, I as a user and then I'm going to
[00:13:15] make this public so you guys can
[00:13:16] literally submit GitHub issues as well.
[00:13:18] It's going to be so fun when I get this
[00:13:20] really running.
[00:13:21] And the input is a GitHub issue. And so,
[00:13:23] this is either a bug that we've noticed
[00:13:25] in the platform as we've tested it as a
[00:13:27] user or it's a new feature that we're
[00:13:29] requesting the Dark Factory to add into
[00:13:31] the codebase.
[00:13:33] So, we create a set of GitHub issues
[00:13:35] like maybe there's you know 20 that are
[00:13:37] created in the last hour or something
[00:13:39] like that. And then on a scheduled
[00:13:41] basis, I'm going to run the first Archon
[00:13:42] workflow. I'm calling it the triage
[00:13:44] workflow. Because the responsibility of
[00:13:47] this Archon workflow
[00:13:49] is to look at all of the GitHub issues.
[00:13:51] And it's going to judge the issues
[00:13:54] against the core governance layer that
[00:13:56] I'm going to build into the the Dark
[00:13:59] Factory repository. So, we're going to
[00:14:02] have our our mission for the repo and
[00:14:04] then the different rules. And these
[00:14:06] files are going to also include the
[00:14:08] scope that we're going to allow for the
[00:14:10] codebase evolution. Like here are
[00:14:12] features that we're definitely not going
[00:14:14] to allow. Here are types of features
[00:14:16] that we are going to allow. So,
[00:14:18] basically the triage workflow
[00:14:21] is going to evaluate all of the GitHub
[00:14:23] issues that were created in the last
[00:14:25] hour, you know, like everything that
[00:14:26] hasn't been triaged yet and it's going
[00:14:29] to figure out like you know, based on
[00:14:31] our mission and rules, what issues
[00:14:33] should we you know, put in a comment and
[00:14:35] close and say like hey, this doesn't
[00:14:37] apply for X Y or Z reason or here's an
[00:14:40] issue that we're going to go into the
[00:14:42] implement step. So, triage and then
[00:14:44] we're going to have a separate Archon
[00:14:46] workflow that goes through the full
[00:14:47] implementation. So, for every single
[00:14:50] issue that we decide we are going to
[00:14:52] address, we're going to invoke Archon
[00:14:54] workflows in parallel to do the full
[00:14:57] implementation.
[00:14:59] And so, again leaning on the beauty of
[00:15:01] Archon here, we can handle any number of
[00:15:03] issues in parallel because it each of
[00:15:06] the issues are going to be handled in a
[00:15:08] a work tree. So, we have full isolation,
[00:15:10] full copy of the codebase for each one
[00:15:13] of the issues to be worked on
[00:15:15] independently without stepping on each
[00:15:17] other's toes. So, we implement and then
[00:15:19] for every single one of the issues that
[00:15:22] we addressed, either a bug that we fixed
[00:15:24] or a feature that we built, we're going
[00:15:26] to have a separate Archon validate
[00:15:28] workflow. So, this is where we do the PR
[00:15:30] review before we do the merge into main.
[00:15:34] And one of the things that Strong DM
[00:15:36] implemented in their Dark Factory that's
[00:15:37] very powerful is
[00:15:40] what they call the holdout pattern.
[00:15:42] So, the holdout pattern is the idea that
[00:15:46] we don't want the bias from the
[00:15:48] implementation to go into the testing.
[00:15:51] And this is such a prevalent problem
[00:15:54] with coding agents in general is they
[00:15:57] will if you ask it to check its own
[00:15:59] work, it's like asking a student to
[00:16:02] check their own homework. They might you
[00:16:05] know, give a little bit of feedback just
[00:16:07] to seem like they're they are being
[00:16:08] critical of themselves, but in the end
[00:16:10] their bias is going to win out and
[00:16:12] they're going to stuff the bigger
[00:16:13] problems under the rug.
[00:16:15] And so, what we do is a handoff. After
[00:16:17] the implementation, we go through all of
[00:16:19] our testing scenarios, but we don't tell
[00:16:22] the validation agent what was just
[00:16:24] implemented. So, we basically just do
[00:16:26] regression testing over the entire
[00:16:27] system. So, that way there's no chance
[00:16:30] of bias cuz it doesn't even know like
[00:16:32] what the issue was meant to address.
[00:16:34] >> [clears throat]
[00:16:35] >> And that sounds kind of risky and like
[00:16:37] honestly myself, I'm not fully convinced
[00:16:39] of this, but that that is Strong DM's
[00:16:41] holdout trick and we're going to try
[00:16:42] building that as well. That's why we
[00:16:44] have a separate workflow for validation
[00:16:46] and we don't just have it built into the
[00:16:47] implementation.
[00:16:49] Now, in Archon you can just like you
[00:16:51] know, start fresh sessions between
[00:16:53] nodes. So, I guess we could package this
[00:16:55] up as one workflow and still have the
[00:16:56] holdout pattern. Um that's one of the
[00:16:58] things I'll just kind of have to explore
[00:16:59] as I'm building with you guys. Like I'm
[00:17:01] setting a lot of this up from scratch.
[00:17:03] Like this is a live coding session. Like
[00:17:04] I said, I'm not presenting something
[00:17:07] that I've already built like I did with
[00:17:09] Archon in the last live stream.
[00:17:12] So, yeah, uh that's pretty much the
[00:17:14] workflow here. So, I mean really it just
[00:17:16] comes down to we have the governance
[00:17:17] layer. These are pieces of context we're
[00:17:20] always going to inject into every Archon
[00:17:22] workflow. And then we have Archon
[00:17:24] workflows to handle the full
[00:17:25] orchestration here. Triage, implement,
[00:17:27] validate, and fix.
[00:17:30] And as far as the repository that this
[00:17:32] is going to operate on,
[00:17:34] it is going to be uh this one right
[00:17:36] here. So, obviously I'm not going to use
[00:17:38] Archon to work on Archon here. I don't
[00:17:42] want to turn Archon into a Dark Factory
[00:17:44] repository. It is too important that
[00:17:46] that this doesn't just become an
[00:17:47] experiment. So, there's a separate repo,
[00:17:49] a separate project that I'm going to
[00:17:51] build using the Archon workflows in the
[00:17:53] Dark Factory.
[00:17:55] And uh it's actually a pretty cool um
[00:17:58] application. Like this is going to be a
[00:18:00] huge value add for my YouTube channel
[00:18:02] cuz essentially it's going to be a chat
[00:18:05] platform, an agentic chat platform where
[00:18:07] you can ask it any kinds of questions
[00:18:09] around AI and then it's going to perform
[00:18:11] rag. It's going to search through my
[00:18:13] YouTube videos to give you an answer.
[00:18:15] So, it's kind of like your own AI tutor
[00:18:17] based on my content.
[00:18:19] And then I was also thinking about doing
[00:18:21] something for the Dynamis community. If
[00:18:23] you are in the Dynamis community, you
[00:18:25] can connect your account into this
[00:18:27] platform. So, then not only would it
[00:18:28] search over my YouTube content, but it
[00:18:30] would also search over my workshops and
[00:18:33] courses that I have in the community.
[00:18:34] So, it'd become like the ultimate AI
[00:18:36] tutor. So, it'd be like available to
[00:18:38] everybody, but then it'd be even like a
[00:18:39] nice value add to the Dynamis as well.
[00:18:41] So, I'm actually really excited to build
[00:18:43] this out. Um and so, if the Dark Factory
[00:18:45] experiment doesn't work for whatever
[00:18:47] reason, um and like I have faith in it,
[00:18:50] but it is very risky. Like so, if it
[00:18:52] doesn't really like build on anything
[00:18:54] that like works super super well, then
[00:18:56] I'm just going to you know, build it
[00:18:57] myself with my usual AI coding process
[00:19:00] cuz I want to have this by the end of
[00:19:01] the month for everyone.
[00:19:02] Uh but we'll see if the Dark Factory can
[00:19:04] manage everything cuz I'm going to work
[00:19:06] hard to build that initial AI layer. Um
[00:19:10] let me actually refresh here cuz I I
[00:19:11] already created the mission factory
[00:19:13] rules in claw.md.
[00:19:15] So, I'm going to work hard to build out
[00:19:17] the
[00:19:18] the governance [clears throat] layer,
[00:19:19] build out the Archon workflows. I want
[00:19:21] to make this as reliable as possible.
[00:19:25] Now, the biggest risk that we have to
[00:19:27] this Dark Factory
[00:19:30] is that I can't actually use my
[00:19:33] Anthropic subscription
[00:19:36] because I would hit my rate limits way
[00:19:38] too fast.
[00:19:39] And if I want to make this public so
[00:19:42] anybody can create GitHub issues
[00:19:45] for the Dark Factory, I believe that
[00:19:47] would be against the Anthropic terms of
[00:19:49] service
[00:19:51] if I let other people's GitHub issues
[00:19:53] get automatically consumed into the
[00:19:54] system, cuz then it's essentially other
[00:19:56] people being able to use my Anthropic
[00:19:58] subscription, because I'm not the one
[00:20:01] starting the workflow. It's like
[00:20:03] technically another user, I think. I
[00:20:05] just want to be careful there. And I'd
[00:20:07] hit my rate limits way too fast anyway.
[00:20:09] So, I can't actually use my Anthropic
[00:20:12] subscription for the Dark Factory.
[00:20:15] And so, what that means is I have to pay
[00:20:16] for an API.
[00:20:18] I have to pay per token
[00:20:20] for everything I have built in this that
[00:20:23] I'm going to build in this Dark Factory.
[00:20:25] And unfortunately, Opus would be way too
[00:20:28] expensive.
[00:20:30] So, I have to resort to other means. And
[00:20:34] actually, what I came up with
[00:20:36] is I'm going to use MiniMax M2.7
[00:20:40] as the large language model driving the
[00:20:42] entire Dark Factory.
[00:20:46] Now, um
[00:20:48] I've done a lot of research for
[00:20:49] different models. I considered Qwen 3.5
[00:20:52] Coder. I considered GLM 5.1. I thought
[00:20:56] about maybe using like Sonnet, but
[00:20:58] Sonnet would be too expensive. Um I was
[00:21:01] maybe going to use Sonnet through
[00:21:02] OpenRouter or just the Anthropic API
[00:21:04] directly. Haiku would definitely be not
[00:21:07] powerful enough. So, I I can't really
[00:21:09] use an Anthropic model, right? Cuz like
[00:21:11] Opus and Sonnet are too expensive. Haiku
[00:21:13] is like significantly worse than MiniMax
[00:21:15] M2.7, and they're actually a pretty
[00:21:17] similar cost, I believe. Um yeah, cuz
[00:21:20] like
[00:21:21] if I go to OpenRouter here
[00:21:24] and I search for Claude Haiku 3 or 4.5,
[00:21:28] it is
[00:21:30] um
[00:21:30] $1 for every 1 million input tokens.
[00:21:34] It's actually more expensive than um
[00:21:37] MiniMax M2.7. That This It's less than a
[00:21:41] dollar. Yeah, it's only 30 cents for
[00:21:43] every 1 million input tokens. So, it's a
[00:21:45] third of the price of Haiku and way
[00:21:47] better. So, there's no reason if I'm not
[00:21:48] going to use my Anthropic subscription,
[00:21:50] there's no reason for me to actually use
[00:21:52] an Anthropic model, because Opus and
[00:21:55] Sonnet would be way too much.
[00:21:57] And so, yeah, I I did a lot of research
[00:21:59] and this is what I landed on. And I can
[00:22:01] always switch the entire system, but
[00:22:03] what I've done here
[00:22:05] and this is part of the the setup that
[00:22:07] I've already taken care of automat or
[00:22:08] behind the scenes is I already have a
[00:22:11] VPS spun up where I have Archon
[00:22:14] installed. I have the rag YouTube chat
[00:22:18] application cloned and and configured.
[00:22:21] And then I have my Claude code
[00:22:24] changed there
[00:22:26] to use MiniMax M2.7 instead of
[00:22:30] Anthropic. So, if I ask like here, give
[00:22:33] me the SSH command. I'll actually show
[00:22:35] you guys. I'll SSH into the machine live
[00:22:38] with you and show you what it looks
[00:22:40] like. So,
[00:22:41] all right. I'll grab this command here.
[00:22:46] All right.
[00:22:48] Cuz take a look at this. If I go into
[00:22:51] Claude,
[00:22:53] I open [snorts] up Claude while I'm SSH
[00:22:55] into this machine,
[00:22:57] you can see that it's using MiniMax
[00:22:59] M2.7. And if I say, you know, like what
[00:23:01] model are you, everything looks like I'm
[00:23:03] using Claude, but
[00:23:06] or that I'm using Claude code normally,
[00:23:07] but it is actually going and and using
[00:23:10] my MiniMax API key and running on M2.7.
[00:23:14] And by the way, if I wanted to use like
[00:23:16] GLM 5.1 instead, it would be super easy.
[00:23:19] Like I could swap over in like 30
[00:23:21] seconds,
[00:23:22] because all you have to do to swap the
[00:23:25] provider for Claude code is you just
[00:23:27] have to change a couple of environment
[00:23:29] variables under the hood. Like And And
[00:23:31] by the way, this session that I have
[00:23:32] open with Claude code, this is on my
[00:23:33] local computer where I'm doing some
[00:23:36] setup locally. And what I had in the
[00:23:39] session, I had it read my whole Dark
[00:23:40] Factory plan. So, like everything you
[00:23:43] see right here, it has loaded into the
[00:23:44] context currently. So, I can just ask it
[00:23:46] here, don't show any secrets, but tell
[00:23:49] me exactly how I changed Claude code to
[00:23:52] use MiniMax M2.7 instead of Anthropic
[00:23:55] for the model.
[00:23:57] Um so, I I might actually open source my
[00:24:00] entire Dark Factory plan. Cuz as I've
[00:24:02] been setting things up behind the
[00:24:03] scenes, I've just been like documenting
[00:24:05] everything in this like pretty massive
[00:24:07] file here, including all of the Archon
[00:24:09] workflows that I'm going to build with
[00:24:11] you guys live right now. So, I have a
[00:24:13] plan initially for every single one of
[00:24:15] these. So, we'll build them today and
[00:24:16] test them and maybe get to the point
[00:24:18] where we have the whole Dark Factory
[00:24:20] running. I'm not sure if we'll get that
[00:24:21] far, cuz it's going to be quite a bit of
[00:24:23] setup. Um but yeah, you can see that uh
[00:24:26] for switching the provider for Claude
[00:24:29] code, you just have to set these
[00:24:31] environment variables. There There's
[00:24:33] quite a bit here.
[00:24:35] So, I think it actually would be pretty
[00:24:36] useful to share this with you guys. Uh
[00:24:38] cuz there were there was a
[00:24:40] It was a little bit trickier than I
[00:24:41] thought it would be to switch the
[00:24:43] provider. Uh because then you The other
[00:24:46] thing you have to do for Archon is you
[00:24:48] have to map the environment variables
[00:24:50] for the different model types. Cuz in
[00:24:53] Archon, you know, for each of the
[00:24:54] workflows, you can specify like for this
[00:24:57] node, I want to use Sonnet. Or this
[00:24:58] node, I want to use Haiku. And so, to
[00:25:01] make the Archon workflows work out of
[00:25:03] the box without having to change these
[00:25:05] IDs, you just have to map it through
[00:25:07] environment variables. So, like when I
[00:25:09] specify Opus in Claude code or in an
[00:25:11] Archon workflow,
[00:25:13] that maps to MiniMax M2.7. Same thing
[00:25:16] with Sonnet. And then if I want to use
[00:25:17] Haiku, then it maps to MiniMax M2.7 high
[00:25:21] speed, right? So, just a faster and
[00:25:23] cheaper version of 2.7. So, I have the
[00:25:26] same effect in an Archon workflow where
[00:25:28] I can make some things a lot faster, and
[00:25:31] then other things I have the most power
[00:25:33] I possibly can.
[00:25:35] Um like if I typically would use Opus or
[00:25:37] maybe Sonnet.
[00:25:39] So, yeah, if you are interested in using
[00:25:42] Claude code with a different provider,
[00:25:44] it's actually quite easy to set up. So,
[00:25:47] you could have it use OpenRouter if you
[00:25:48] want to use the Anthropic models there.
[00:25:50] Um GLM has an Anthropic compatible
[00:25:53] endpoint.
[00:25:54] Um of course, MiniMax does as well. I
[00:25:57] think Qwen does. Does Qwen have a Claude
[00:26:01] code compatible endpoint? And if you
[00:26:04] want to run local models with Claude
[00:26:07] [snorts] code, you can use Ollama as
[00:26:09] well. So, Ollama has a direct
[00:26:12] integration with Claude code. So, it's
[00:26:15] kind of cool, because we are planning on
[00:26:16] adding Pi support this week for Archon.
[00:26:19] So, you can run all of your workflows
[00:26:20] through Pi agents.
[00:26:22] And but even right now, you are able to
[00:26:25] immediately switch Claude code to use
[00:26:27] any models, so that you don't
[00:26:28] necessarily have to lean on another
[00:26:30] provider, but you're not stuck to using
[00:26:32] your Anthropic subscription or the
[00:26:33] Anthropic API key.
[00:26:38] Okay.
[00:26:40] Um
[00:26:42] let's see.
[00:26:43] Yeah, I don't think Qwen has Okay, but
[00:26:45] like GLM and MiniMax
[00:26:47] have the Anthropic compatible endpoints.
[00:26:52] So, yeah, just ask Claude to do some
[00:26:54] research for you. See like which ones
[00:26:56] are compatible with Claude code, but
[00:26:57] most models you're able to use directly,
[00:27:00] like I set up with MiniMax here.
[00:27:04] All right.
[00:27:06] See what it says here. Yep, see yeah,
[00:27:08] GLM has a first-party Anthropic
[00:27:10] compatible endpoint. So, it's like
[00:27:11] literally their API endpoint, and then
[00:27:13] you just add Anthropic at the end. So,
[00:27:15] that that's what you hit when you want
[00:27:17] to make it compatible with Claude code.
[00:27:19] So, pretty cool. It's It's pretty easy
[00:27:21] to set it up.
[00:27:23] All right.
[00:27:25] Cool. So, uh yeah, I want to get into
[00:27:27] building with you guys here.
[00:27:29] Let me check the context. Maybe I'll
[00:27:31] spend a little bit of time to answer you
[00:27:32] guys' questions. So, I know I haven't
[00:27:34] really looked at the chat yet.
[00:27:35] Definitely want to do that. So, I'll
[00:27:37] I'll spend a little bit of time doing
[00:27:38] that, and then we can get right into
[00:27:40] building out our factory. So, going to
[00:27:42] the diagram here, I already have the
[00:27:44] governance layer built out. And then as
[00:27:46] I'm creating the workflows, I'll show
[00:27:48] you guys what that looks like. So, right
[00:27:50] now, I mostly just need to build out the
[00:27:52] Archon workflows.
[00:27:54] And it's important for all the Archon
[00:27:56] workflows to like actually ingest these
[00:27:59] documents here. Like it needs to know
[00:28:01] like no matter what workflow I have
[00:28:02] running, if I'm fixing something,
[00:28:04] validating something, whatever, like it
[00:28:05] has to always know the mission and
[00:28:07] factory rules, cuz that's going to be
[00:28:09] the primary guidance. And then I mean,
[00:28:10] of course, the global like the Claude.md
[00:28:13] as well.
[00:28:15] So, yes, I am doing everything through
[00:28:16] Claude code, but
[00:28:18] I mean, you could easily make this Dark
[00:28:19] Factory do like you use Code X or
[00:28:22] OpenCoder Pi instead, but
[00:28:25] yeah, it's just what I'm using. I like
[00:28:26] using Claude code as a harness, even if
[00:28:28] I'm not using Anthropic models.
[00:28:31] All right. Cool. So, yeah, I'll leave
[00:28:33] this up, and then I'll I'll go ahead and
[00:28:34] hit some questions from the chat here.
[00:28:38] And the future begins. That's right.
[00:28:40] That's what we're building. We're
[00:28:41] building the future here. I don't think
[00:28:43] that that the Dark Factory is a pattern
[00:28:45] that's reliable enough right right now,
[00:28:47] but if we refine the workflows enough,
[00:28:50] and if we have We'd probably need more
[00:28:51] powerful models as well, honestly, to
[00:28:53] like really make this production ready,
[00:28:55] but maybe Mythos is going to be the
[00:28:56] unlock. We'll see.
[00:29:01] All right.
[00:29:03] I'm level -11 or -1, not from a tech
[00:29:06] background at all.
[00:29:08] I mean, that's all good, cuz with how
[00:29:10] powerful AI coding assistants are right
[00:29:12] now,
[00:29:13] you can get to level three
[00:29:16] very very quickly.
[00:29:18] And in fact, if you don't have a tech
[00:29:20] experience, you probably won't ever be
[00:29:22] level zero through level two, because
[00:29:24] that requires you to write code yourself
[00:29:25] sometimes. And so, these days when you
[00:29:28] learn how to leverage AI coding
[00:29:30] assistants and you're not coming from a
[00:29:31] technical background, you just jump
[00:29:33] right into level three.
[00:29:35] My big recommendation with that though
[00:29:36] is to ask your coding agent a lot of
[00:29:38] questions as it's creating code for you,
[00:29:40] so that you can start to gain an
[00:29:41] understanding and like, you know, sort
[00:29:43] of become at least semi-technical
[00:29:45] yourself as you're using the tools.
[00:29:50] Um will this video be saved for later?
[00:29:53] Uh 100% Lennart's, yeah. So, every
[00:29:55] single live stream on YouTube is
[00:29:56] automatically turned into a recording
[00:29:58] after. So, I don't even have to like
[00:29:59] upload it myself. And so, I think it
[00:30:02] takes a little bit of processing time,
[00:30:03] but like what we have right here, it
[00:30:05] says live right now, it'll be turned
[00:30:06] into another video just like my live
[00:30:08] stream this weekend. So, you just have
[00:30:09] to go to the live tab. It's not in the
[00:30:11] main video tab for my long-form content.
[00:30:14] You just go over here
[00:30:16] and then it'll be available for you.
[00:30:19] All right.
[00:30:26] I still feel like I need to test things
[00:30:27] myself. I don't yet trust AI to test and
[00:30:30] uh especially ship. I'm with you there.
[00:30:34] Yeah, like I said, level three is where
[00:30:35] it's at when you really care the most
[00:30:37] about reliability. Unless you've built
[00:30:40] some kind of level four harness that you
[00:30:42] really really have faith in, I would
[00:30:44] generally recommend sticking to level
[00:30:46] three. And then level five is like no
[00:30:49] one really knows how much this is really
[00:30:51] going to work at this point. And that's
[00:30:53] what I want to find out with you guys.
[00:30:54] Like yeah, we have examples like strong
[00:30:56] DM,
[00:30:57] but they haven't they they've not really
[00:30:59] shared that much, right? And like a lot
[00:31:01] of it could just be like marketing hype.
[00:31:03] So, that's what I want to figure out for
[00:31:04] you guys for reals. Like if we actually
[00:31:06] put a lot of effort into using Archon
[00:31:08] and uh building a lot of reliability
[00:31:10] through a governments layer, like how
[00:31:11] reliable can we really make it? And I'm
[00:31:13] excited to find out. We're going to do
[00:31:15] it together.
[00:31:19] Um you don't trust that if it's secure
[00:31:22] or more than everything is working. I
[00:31:23] mean,
[00:31:24] okay, so sorry, this is a question
[00:31:26] follow-up from the other one. But yeah,
[00:31:28] I mean, I I would say personally that
[00:31:29] like security is a big concern for AI
[00:31:32] coding assistants. They do introduce
[00:31:33] more security issues than uh seasoned
[00:31:37] engineers. Um they can valid they can
[00:31:40] fix them as well, but like first pass,
[00:31:42] they introduce more. Um and then yeah,
[00:31:44] just like generally that everything is
[00:31:45] actually working. Cuz okay, here's the
[00:31:47] other problem with AI coding assistants.
[00:31:49] And then honestly, probably the main
[00:31:51] reason that level five might fail, it's
[00:31:54] not necessarily that the coding agent
[00:31:56] produces code that fails, but it's more
[00:31:58] that it's just not aligned with what you
[00:32:00] want to create.
[00:32:02] And that's part of why I'm going to be
[00:32:03] focusing so much up up front on building
[00:32:05] the governments layer because I need to
[00:32:08] be very clear on the guardrails and the
[00:32:11] guidelines for the coding agent so that
[00:32:13] when it picks up an issue and implements
[00:32:16] it,
[00:32:17] uh first of all, I want to make sure the
[00:32:19] issue is actually aligned with what I
[00:32:20] want for the code base, for the
[00:32:22] evolution of it. And then also like when
[00:32:24] it does the implementation itself, it
[00:32:25] doesn't misunderstand what the issue is
[00:32:27] really getting at. Like if I open an
[00:32:29] issue because I want to improve the rag
[00:32:32] search, I don't want it to like change
[00:32:34] the front end. I want it to just like
[00:32:36] change the rag pipeline, for example.
[00:32:41] All right.
[00:32:43] See what else we got here in the chat.
[00:32:47] Um I presume the dark factory can
[00:32:49] introduce bugs later down the line if
[00:32:51] proper unit testing, linting, and bug
[00:32:53] regression system is is set up
[00:32:54] correctly.
[00:32:57] Um so, yeah, that's going to be one of
[00:32:59] the risks of the dark factory as well as
[00:33:01] there might be little problems that
[00:33:03] creep in that our validation doesn't
[00:33:05] catch and they might blow up in our face
[00:33:07] later on. That's one of the reasons
[00:33:09] human in the loop is so important for
[00:33:11] reviewing things is to catch those
[00:33:13] little issues that become a bigger
[00:33:15] problem later.
[00:33:17] Um so, the dark factory could kind of be
[00:33:19] like boiling a frog in water, right?
[00:33:21] Like the frog, if you put a frog in
[00:33:23] scalding hot water, it's going to
[00:33:26] immediately jump out of the pot.
[00:33:28] And so, the analogy here is like if we
[00:33:30] have a massive issue in the code base
[00:33:33] right after implementation,
[00:33:35] the validation is going to catch that
[00:33:37] and it's going to address it. But if
[00:33:38] it's something that slips under the
[00:33:39] crack cuz it's not super apparent right
[00:33:41] away, it's like the frog that you put in
[00:33:43] warm water and then you boil it over
[00:33:45] time. And so, it stays there until it's
[00:33:47] dead.
[00:33:48] >> [laughter]
[00:33:48] >> Right? Like that could happen to a dark
[00:33:50] factory. You have these these little
[00:33:51] issues that creep in over time. It's not
[00:33:53] big enough for the validate agent to
[00:33:55] catch it, but then they combine together
[00:33:58] to produce bigger problems or it's just
[00:34:00] an issue that compounds on itself and
[00:34:02] you're not there in the loop to find
[00:34:04] those things and correct those things.
[00:34:05] So, it's certainly possible. And uh as
[00:34:08] much as we can, that's why it's it's
[00:34:11] important for us to build a very
[00:34:12] comprehensive validation process. Not
[00:34:15] just with unit testing and linting, but
[00:34:17] I'm going to be building in like full
[00:34:18] regression testing. Like every single
[00:34:20] time we handle an issue, I want the
[00:34:22] validation to use a browser automation
[00:34:25] tool to go through the rag chat
[00:34:28] application like just like a user would.
[00:34:31] And um like test this whole interface
[00:34:33] and have different conversations and
[00:34:34] click on the sources that it sites and
[00:34:36] make sure that goes to the right part of
[00:34:37] a YouTube video. Like I it's got to be
[00:34:39] doing everything and constantly kind of
[00:34:41] like maintaining this list of features
[00:34:43] that it needs to test every time it's
[00:34:45] doing proper regression testing.
[00:34:48] So, we'll get there. That's going to be
[00:34:49] probably one of the biggest challenges
[00:34:50] to build for this whole thing.
[00:34:57] All right.
[00:34:59] Um also, it would be handy if you can
[00:35:01] suggest open source or free alternatives
[00:35:03] if available out there for the tools
[00:35:05] we're using. As a learner, those crazy
[00:35:07] bills make my heart sink. I'm with you.
[00:35:09] I understand the pain for sure.
[00:35:11] So, I I guess I'm curious like what
[00:35:13] tools you're referring to exactly. If
[00:35:15] you're talking about AI coding
[00:35:16] assistants,
[00:35:18] unfortunately, there's not really a a
[00:35:20] free alternative to something like
[00:35:22] Claude Code that's just as good as
[00:35:23] Claude. Like I was talking about
[00:35:25] earlier, I'm using Minimax M2.7 instead
[00:35:28] of Opus cuz it's a lot cheaper. It's
[00:35:30] still not going to be as powerful.
[00:35:32] And if you really want like free AI
[00:35:35] coding, then my recommendation is to run
[00:35:38] a model in Claude Code through Ollama.
[00:35:41] Like you can run Gemma 4, um Qwen 3 has
[00:35:44] some smaller good models. You're not
[00:35:46] going to get nearly as good of results
[00:35:47] as Opus though. But like it is possible
[00:35:50] to do AI coding free. You just have the
[00:35:53] expectation that um you can't do the
[00:35:55] same things that you can do with Opus or
[00:35:58] some other more powerful model like
[00:36:00] GPT-5.4 Codex in uh Codex, for example.
[00:36:05] So.
[00:36:06] All right.
[00:36:12] Let's see.
[00:36:14] Got only 1 year to experiment.
[00:36:17] Oh, let's see. The comment above. I'm
[00:36:18] thinking of creating some kind of
[00:36:20] architecture for local businesses here
[00:36:22] so I can and provide them. So, got to be
[00:36:24] safe, easy to set up and manage for them
[00:36:25] and myself and I don't get sued.
[00:36:28] I have I'm curious what kind of
[00:36:29] architecture you're talking about. Like
[00:36:31] if it's an agentic system or if it's um
[00:36:34] like if it's an AI agent or like for AI
[00:36:36] coding.
[00:36:37] Sounds cool though.
[00:36:41] All right.
[00:36:45] Gemini makes a good evaluator to run
[00:36:48] against Claude.
[00:36:49] Yeah, that is one of the things I want
[00:36:51] to be experimenting in with Archon soon
[00:36:53] is building workflows that combine
[00:36:55] providers
[00:36:56] so that we can do like exactly what
[00:36:58] you're describing. Like Claude for
[00:36:59] implementation and then Gemini, a lot of
[00:37:01] people like using Codex for review as
[00:37:03] well just to to have a
[00:37:05] check on Claude. Um so, yeah, that's
[00:37:08] going to come soon for Archon.
[00:37:11] All right.
[00:37:15] Cool cool.
[00:37:17] Um
[00:37:22] Was that Excalidraw in Obsidian?
[00:37:26] Yes. My Excalidraw diagrams I always
[00:37:28] have in Obsidian.
[00:37:30] So, I'll show you that really quick. If
[00:37:32] I go to the settings and go to my
[00:37:34] community plugins here,
[00:37:36] I use I just use the Excalidraw plugin
[00:37:40] by uh Zsolt. I don't know if I'm saying
[00:37:43] that [laughter] right. But yeah, I've
[00:37:45] used this for a long time now.
[00:37:47] Very very good. Cuz I just want to have
[00:37:49] everything in my vault together.
[00:37:51] Diagrams, research, everything. So, I
[00:37:53] love using this plugin all the time.
[00:37:58] All right.
[00:38:01] Cool.
[00:38:02] So, it little paywalled after all. Let's
[00:38:04] see.
[00:38:06] Right. For AI coding, if you want to get
[00:38:08] the best results, it is paywalled right
[00:38:10] now.
[00:38:11] Um and I mean, unfortunately, it makes
[00:38:14] sense. Like these frontier models like
[00:38:16] Opus and GPT-5.4 Codex, they are
[00:38:19] expensive, man. Like these companies are
[00:38:22] burning through billions of dollars of
[00:38:24] venture capital right now just to have
[00:38:25] these models running for the world and
[00:38:28] they're just starting to like make some
[00:38:29] profits from getting it like the higher
[00:38:32] levels of enterprise agreements.
[00:38:34] Um cuz trust me, they they don't make
[00:38:36] money off of your Anthropic subscription
[00:38:39] if you are really maxing out your rate
[00:38:42] limits for Claude Code.
[00:38:44] Where they're really making the money is
[00:38:46] using you as the lever to get the
[00:38:48] enterprise agreements, the enterprise
[00:38:50] interest.
[00:38:51] So, they're they're profitable,
[00:38:54] but it's it's very subsidized for our
[00:38:56] Anthropic subscriptions. And that's part
[00:38:58] of why they're
[00:38:59] um jacking down the rate limits right
[00:39:01] now. It's kind of unfortunate. It's uh
[00:39:04] I'm not I'm not able to get nearly as
[00:39:06] much out of Claude Code with my
[00:39:08] Anthropic subscription compared to even
[00:39:09] like a couple weeks ago.
[00:39:11] Um the rate limits are are worse now,
[00:39:13] unfortunately.
[00:39:16] And they took away my 1 million token
[00:39:18] Claude Code. That's another thing that
[00:39:20] I'm kind of frustrated by. Um like if I
[00:39:22] if I do slash model, apparently some
[00:39:25] people still have this. So, I don't know
[00:39:27] why it's just me, but I don't have the
[00:39:30] option to use a 1 million Opus or or uh
[00:39:32] Sonnet anymore.
[00:39:35] So, I'd be I'd be curious if anyone else
[00:39:37] has run into this as well.
[00:39:40] But I am stuck to 200,000 tokens again
[00:39:43] as of like just 3 days ago.
[00:39:45] I don't know why. Or maybe it was like a
[00:39:47] week ago.
[00:39:49] But [sighs] yeah.
[00:39:50] Anyway.
[00:39:52] So, yeah. I'm going to have more time to
[00:39:53] answer questions as we are waiting for
[00:39:56] the workflows to be built here.
[00:40:00] Uh one thing I want to put in the chat
[00:40:02] quick is just a link to Archon. So, if
[00:40:05] you're interested in checking out
[00:40:07] Archon, like got some good content
[00:40:09] on my channel.
[00:40:11] Uh got the live stream from the weekend.
[00:40:13] And then also I have the YouTube video
[00:40:16] that I put out just 5 days ago on
[00:40:18] Archon. So, check that out if you're
[00:40:19] interested. Like I said, because I've
[00:40:21] already done so much content, I'm not
[00:40:22] going to be like hyper focused on
[00:40:24] explaining Archon. I'm going to get
[00:40:25] quick pretty quick here just into doing
[00:40:28] [snorts] a live coding session creating
[00:40:30] the Archon workflows with you guys.
[00:40:33] Um and then also the repository that I'm
[00:40:36] using the Dark Factory to build, this is
[00:40:39] private for now.
[00:40:42] Um well, no actually I made it public.
[00:40:44] But, I'm not going to make it so that
[00:40:45] you can give any issue to the Dark
[00:40:48] Factory yet.
[00:40:50] So, I'm going to start by having it only
[00:40:51] accept issues from me.
[00:40:53] And um then I'll make it so it's
[00:40:56] available to everyone after I've like
[00:40:58] tested things for about a week is my
[00:41:00] plan. Something like that.
[00:41:02] In fact, I I might actually want to make
[00:41:03] this repo private right now.
[00:41:06] As I build this as a safety measure.
[00:41:08] We'll see. I I might have to switch it
[00:41:10] private until I'm like confident that it
[00:41:12] really is only handling my own issues.
[00:41:15] >> [laughter]
[00:41:15] >> So, we'll we'll have to
[00:41:18] do that in a little bit. But, let's
[00:41:19] start by building the Archon workflows
[00:41:20] here.
[00:41:23] Okay.
[00:41:24] So, in my chat, how much do I have?
[00:41:26] Okay, I have 40% of my context used. So,
[00:41:28] I should be good to continue here.
[00:41:32] So, again this conversation that I have,
[00:41:35] it already has my full Dark Factory plan
[00:41:38] loaded.
[00:41:40] And so, I can literally just ask it like
[00:41:41] what should I build next? Because I've
[00:41:43] been keeping a log of everything that
[00:41:45] I've created as I built it. So, like for
[00:41:48] example, one thing that I already did is
[00:41:50] I created the core governments uh doc
[00:41:54] governance documents. So, I have like my
[00:41:56] mission.md, factory rules. I can show
[00:41:59] that to you guys like a little bit of
[00:42:00] what went into that um as the workflow
[00:42:03] is building. I just want to be efficient
[00:42:04] with the time here.
[00:42:07] All right.
[00:42:09] So,
[00:42:13] So, there's some things that I was doing
[00:42:14] during an event in the Dynamis
[00:42:16] community.
[00:42:17] And then uh here's the remaining punch
[00:42:20] lists from section 14. I told you it's
[00:42:22] comprehensive. Section 14 of the plan.
[00:42:25] Uh ordered by what makes sense to build
[00:42:27] now and save for live.
[00:42:30] Okay, so I guess there's a couple of
[00:42:31] things that it recommended that I do
[00:42:33] before the live stream here.
[00:42:35] But also these are going to be super
[00:42:36] quick
[00:42:37] to set up anyway.
[00:42:39] We need to create the GitHub labels, um
[00:42:41] the issue and PR template, orchestration
[00:42:44] shell script.
[00:42:46] Yeah, I'm going to
[00:42:49] Yeah, I'm going to have it rip through
[00:42:50] all these things in parallel. So, okay.
[00:42:52] The GitHub labels are actually kind of
[00:42:54] interesting because everything in the
[00:42:56] Dark Factory is going to be managed
[00:42:58] through labels. So, when the triage
[00:43:00] workflow runs, it's going to basically
[00:43:02] check on these labels as a status. Like
[00:43:05] this thing is currently being
[00:43:06] implemented, right? Like don't don't
[00:43:08] send off another Archon workflow to work
[00:43:10] on this because it's already in
[00:43:12] progress.
[00:43:14] Or
[00:43:15] worst case scenario, if it fails to
[00:43:17] implement the pull request two times in
[00:43:18] a row,
[00:43:19] I'm going to have it labeled needs
[00:43:21] human.
[00:43:22] So, maybe I'm not making this like fully
[00:43:24] fully Dark Factory, but I do want to at
[00:43:26] least have like a small escape if I
[00:43:29] really need to address something myself.
[00:43:31] So, I have a little bit of a system
[00:43:33] created for that.
[00:43:34] And then uh yeah, like if I reject an
[00:43:36] issue, like this doesn't fit with our
[00:43:37] mission, or if I approve it and we're
[00:43:39] not going into implementation yet, then
[00:43:40] I'll add that label.
[00:43:42] Um and then factory rate limit, I'm
[00:43:44] going to have some protection to make
[00:43:45] sure I don't blow through like hundreds
[00:43:47] of dollars of Minimax credits in a day.
[00:43:50] And so, if we need to wait for the next
[00:43:52] day for the rate limits to subside that
[00:43:53] I'm going to build into the system, then
[00:43:55] we'll add this label as well. So,
[00:43:57] yeah. It's a hard even in a live stream
[00:43:59] to get like super deep into everything
[00:44:01] that I planned here. But, I hope that
[00:44:02] you can see from the the label system
[00:44:04] that I have for these GitHub issues,
[00:44:06] like there's a lot of thought that I put
[00:44:09] into this system even handling like rate
[00:44:11] limits and human escape if I really
[00:44:14] really need it.
[00:44:16] Um so, yeah. Really like the important
[00:44:18] thing here is the GitHub issues are
[00:44:20] driving the entire Dark Factory. Because
[00:44:23] any kind of input into the system for a
[00:44:26] bug that needs to be fixed or a feature
[00:44:27] that needs to be created, the input
[00:44:29] comes in from an issue. Whether that's
[00:44:31] me creating it or the Dark Factory
[00:44:34] itself creating the issue. Cuz we do
[00:44:36] also have a sort of feedback loop here
[00:44:38] where when the validation agent runs its
[00:44:40] regression testing, if it encounters any
[00:44:42] problems that are big enough to not just
[00:44:44] be fixed right then and there, then
[00:44:45] it'll create a GitHub issue and then go
[00:44:47] through that loop and then address that.
[00:44:49] And so, anything that it catches in
[00:44:51] regression can just be more issues for
[00:44:53] it to fix autonomously.
[00:44:55] And uh so, yeah. I mean like hopefully
[00:44:57] doesn't mean that we'll hit infinite
[00:44:59] loops of creating issue and issue and
[00:45:00] issue after issue, but might happen.
[00:45:03] That's part of the experiment. We don't
[00:45:04] we don't know what's going to happen or
[00:45:05] what could go wrong. Um but that's why I
[00:45:07] have protections in place to make sure
[00:45:09] that it doesn't um that that just jack
[00:45:12] me up in credits.
[00:45:14] So, yeah. Like when I I have my balance
[00:45:17] here, I I only put like 25 bucks to
[00:45:19] start. And then I've used like, you
[00:45:22] know, 87 cents in my testing so far.
[00:45:24] It's pretty efficient overall.
[00:45:27] But, I'm going to make sure that I um
[00:45:30] yeah, never have like too much like I'm
[00:45:32] I'm disabling auto billing.
[00:45:34] So, that if I run out of credits, I just
[00:45:37] have to manually
[00:45:39] uh add credits and then I'll have the
[00:45:41] system that like detects when issues
[00:45:43] weren't handled cuz of rate limit and
[00:45:44] it'll pick it back up basically.
[00:45:47] Um okay. So, I'm going to say
[00:45:51] uh so, I'll go into my speech-to-text
[00:45:53] tool and I'll say, "I want you to create
[00:45:55] the GitHub labels, issue and PR
[00:45:57] templates, and uh the orchestration
[00:45:59] shell script and cron entry on the VPS.
[00:46:01] So, handle all these right now.
[00:46:05] I'm actually in the middle of the live
[00:46:06] stream now. And so, I will just explain
[00:46:09] the workflows briefly as you do these
[00:46:11] things."
[00:46:13] All right, there we go.
[00:46:15] It still thinks that I'm not in the live
[00:46:16] stream yet. So, I'll give it an update
[00:46:18] of of where I'm actually at.
[00:46:20] >> [laughter]
[00:46:21] >> Claude code doesn't really have a sense
[00:46:22] of time.
[00:46:25] Okay. So, while that runs,
[00:46:30] who's paying for all this quota context?
[00:46:33] I'm paying for it. It's it's coming out
[00:46:35] of pocket, which is why I'm using
[00:46:36] something very cheap like Minimax M2.7.
[00:46:40] Yep.
[00:46:42] Okay. So, let's see. Let's go back to
[00:46:45] the Dark Factory plan. I want to show
[00:46:48] you guys a little bit of what the Archon
[00:46:50] workflows will probably look like. So,
[00:46:53] what I have here,
[00:46:55] these are very much rough drafts of the
[00:46:58] Archon workflow. So, when I actually
[00:47:00] build them in a little bit in our stream
[00:47:02] here, they might end up looking quite
[00:47:03] different.
[00:47:05] But, when I was doing my initial
[00:47:07] planning with Claude code creating this
[00:47:09] whole Dark Factory plan, I also had it
[00:47:12] load the primary Archon skill. So, it
[00:47:15] knows how to build workflows. It knows
[00:47:16] the different parameters, things like
[00:47:18] that, how to use the Archon CLI. So, it
[00:47:21] created the initial draft for them.
[00:47:23] And so, there are four workflows that we
[00:47:26] need in total. We have the triage
[00:47:28] workflow. This figures out what GitHub
[00:47:31] issues we actually want to address and
[00:47:33] it handles the labeling and things like
[00:47:35] that.
[00:47:37] And then uh we have the implementation
[00:47:39] workflow. I have to Gosh, I have to
[00:47:41] scroll a while here. We have the uh
[00:47:44] implementation Wait.
[00:47:46] I already scrolled past it. Where'd it
[00:47:48] go? Where's the header here?
[00:47:51] There might be some malformatting.
[00:47:53] Oh no, here it is.
[00:47:55] Um
[00:47:57] Wait a second.
[00:48:00] Does this do the fix as well? Classify
[00:48:04] apply decisions.
[00:48:06] Oh. I think there might be a misordering
[00:48:08] here. So, okay. Anyway, we also have the
[00:48:10] validate PR workflow. So, this is what
[00:48:12] we're going to run that we're going to
[00:48:15] do the whole like hold out pattern for
[00:48:16] validation. We're going to run this on
[00:48:18] every pull request that's created from
[00:48:19] the workflow that does the issue fix.
[00:48:24] I thought that would be the second one.
[00:48:25] That's why I'm confused right now.
[00:48:27] Um I'm not sure of that. Maybe that
[00:48:29] maybe it just misordered things. So, oh
[00:48:31] oh yeah, it did misorder thing. Okay,
[00:48:33] that's kind of weird. But, anyway, this
[00:48:34] this should be the second workflow. I
[00:48:35] don't know why Claude put it in the plan
[00:48:36] in this order. But, our uh next workflow
[00:48:39] is the one to actually fix.
[00:48:41] Um No, it No, that's not it. This is
[00:48:43] This is a workflow to fix issues that
[00:48:45] happen during PR validation. So, if
[00:48:48] there there are any problems that come
[00:48:50] up when creating the pull or when
[00:48:52] reviewing the pull request, then we run
[00:48:53] this to address things and then push a
[00:48:55] new change to update to the pull
[00:48:57] request.
[00:48:59] Um
[00:49:01] And then we have the
[00:49:03] comprehensive test. So, this is the
[00:49:05] regression testing workflow.
[00:49:07] And this one is going to take a lot of
[00:49:10] tokens. So, I'm planning on running this
[00:49:11] one only like once a day or once a week
[00:49:14] because it's going to look through every
[00:49:16] single possible user journey. Every
[00:49:19] single way we can use the application
[00:49:20] testing every single edge case, making
[00:49:22] sure that it works automatically.
[00:49:24] And then for any things that don't work,
[00:49:26] it's going to create a GitHub issue.
[00:49:28] Right. So, every time we review a pull
[00:49:30] request, we are going to do a lot of
[00:49:32] regression testing, but it's going to be
[00:49:33] a more concise version of this workflow
[00:49:35] cuz this is going to be like pretty
[00:49:36] token heavy.
[00:49:38] And then yeah, I guess the one thing
[00:49:39] that I didn't do is I didn't create the
[00:49:41] workflow for actually fixing the issues.
[00:49:44] And I I sorry, I remember now why that's
[00:49:47] the case. It's because there's a a
[00:49:48] default GitHub fix issue workflow in
[00:49:51] Arkon that I'm just going to use or
[00:49:53] maybe make a little bit of an adaptation
[00:49:55] for. But then for all the other
[00:49:56] workflows, they have to be created from
[00:49:58] scratch. So I apologize like Claude kind
[00:50:00] of confused me here or I forgot the
[00:50:03] planning that I did with it, but
[00:50:05] yeah, we're going to creating the
[00:50:06] workflows in a second here.
[00:50:08] Okay.
[00:50:11] Cool. So all three tasks are done. We
[00:50:13] created the GitHub labels and the issue
[00:50:16] templates
[00:50:17] and then we created the orchestrator. So
[00:50:19] we're we're basically going to create a
[00:50:21] cron job that runs on our VPS every so
[00:50:23] often. And whenever this job triggers,
[00:50:26] it's going to uh basically prompt Claude
[00:50:29] to use the Arkon CLI to invoke the
[00:50:32] workflows. Like, "Okay, it's time to
[00:50:34] triage our issues."
[00:50:35] Or it's time to uh yeah, see this is the
[00:50:37] default one. It's time to fix the GitHub
[00:50:39] issue or it's time to validate the pull
[00:50:41] request.
[00:50:45] So we can go to the GitHub repository
[00:50:46] here and actually check this out.
[00:50:49] So if I refresh
[00:50:51] uh well, here let's go to an issue. And
[00:50:53] if I look at the labels for the issues,
[00:50:56] you can see that we have all these
[00:50:57] labels now. Factory accepted, approved,
[00:50:59] in progress, needs fix, needs human. And
[00:51:02] if we look in the dot GitHub folder, we
[00:51:04] can see the pull request template. We
[00:51:06] want to make sure that as the dark
[00:51:07] factory is operating, it has a set
[00:51:09] standard for what goes into every single
[00:51:12] pull request description and every
[00:51:13] single issue description.
[00:51:15] Because being as consistent as possible
[00:51:17] is one of the best ways to actually make
[00:51:19] this reliable. So we have one template
[00:51:22] for when we're filing a bug,
[00:51:25] one for when we are uh you know,
[00:51:26] requesting a feature. So if I were to
[00:51:28] actually go and open an issue right now,
[00:51:31] uh it asks me, "Is this a bug report, a
[00:51:33] feature request, or should I just create
[00:51:36] it from scratch?" And we're only going
[00:51:37] to uh allow maintainers to to do this
[00:51:40] type. So if I click on a bug report,
[00:51:43] then you can see that it automatically
[00:51:45] populates this form that's defined in
[00:51:48] the template that Claude Code just built
[00:51:50] for me. So now we have some structure.
[00:51:52] We're enforcing certain things because
[00:51:55] we want to make sure like if I'm going
[00:51:56] to have this as a public experiment
[00:51:58] where anybody can open a GitHub issue, I
[00:52:00] I need some kind of expectations set for
[00:52:03] what information you're providing. So we
[00:52:05] have these required fields. So that way
[00:52:06] there is actually enough context for the
[00:52:08] dark factory to address the problem. And
[00:52:11] if a template's not used, then I'm just
[00:52:13] going to instruct the dark factory to
[00:52:15] automatically comment and close the
[00:52:16] issue.
[00:52:17] So we're going to be pretty strict on
[00:52:19] that.
[00:52:22] All right.
[00:52:24] Cool. So uh now we want to actually
[00:52:26] build our workflows here.
[00:52:30] The thing is I'm pretty low on context,
[00:52:31] so I might start a new conversation to
[00:52:33] do this.
[00:52:35] So I'm going to just say
[00:52:36] I'm going to build the Arkon workflows
[00:52:38] in a separate context window. So just go
[00:52:40] ahead and update the plan with what
[00:52:41] we've just done here.
[00:52:43] And then I'll go into a new Claude Code
[00:52:45] session to build the Arkon workflows.
[00:52:48] And while this runs, I can just open up
[00:52:51] a new Claude Code and do that. So let me
[00:52:53] close out of here, open up a new Claude,
[00:52:56] and I'm going to copy the path to the
[00:52:59] full plan.
[00:53:02] I'll just put it at the start of the
[00:53:03] prompt here.
[00:53:06] And then the other thing is uh
[00:53:08] hold on. Let me close out of this. The
[00:53:10] other thing is I want it to
[00:53:13] load the Arkon skill.
[00:53:16] Because I want it to the Arkon skill
[00:53:18] that I have uh it gives a full reference
[00:53:21] to Claude Code uh how to build Arkon
[00:53:24] workflows and best practices for doing
[00:53:26] so.
[00:53:27] And so I'm going to say
[00:53:29] uh read the entire dark factory plan
[00:53:32] that I gave you the path to.
[00:53:34] We are now going to work on building the
[00:53:36] Arkon workflows. And I want to start by
[00:53:38] building the triage, the dark factory
[00:53:41] triage workflow. So
[00:53:44] I also want you to load the Arkon skill.
[00:53:48] Um so you understand all the best
[00:53:49] practices for building Arkon workflows.
[00:53:52] Then I want you to give me a summary of
[00:53:54] your plan for the triage workflow, all
[00:53:57] the nodes, what models we're going to
[00:53:58] use, what the prompts look like.
[00:54:01] I and I want to just like have a
[00:54:02] conversation here iterating on the ideas
[00:54:05] for the workflow before we actually
[00:54:06] build it.
[00:54:08] All right.
[00:54:11] So we're going to do a little bit of a
[00:54:12] pivot loop.
[00:54:13] If you have gone through the Agentic
[00:54:15] Coding Course in Dynalist, you know what
[00:54:16] I'm talking about. We're going to do
[00:54:17] some exploration, some planning up
[00:54:19] front, and then we're going to create
[00:54:21] the workflow and test it.
[00:54:25] I don't even really know how we're going
[00:54:26] to test it exactly, but I'll I'll ask
[00:54:28] for its uh recommendations once we have
[00:54:30] it built. Cuz I might need to kind of
[00:54:32] like
[00:54:34] get the dark factory set up
[00:54:35] incrementally.
[00:54:37] Or maybe I need to like really run the
[00:54:39] triage workflow on the issues I already
[00:54:42] have
[00:54:43] in the repository here and just like see
[00:54:46] what kind of labels it adds and if
[00:54:48] everything's working. And then I'd
[00:54:49] probably have to ask it to also like
[00:54:51] undo all of its work so that we can
[00:54:53] still have like a blank slate of issues
[00:54:54] that aren't aren't uh modeled with yet.
[00:54:57] So we'll see what we have to do once it
[00:54:58] once it builds it here.
[00:55:01] All right.
[00:55:04] Minimax is designed to minimax out those
[00:55:06] credits.
[00:55:08] I hope not. We'll see.
[00:55:09] I'm down to switch to something else
[00:55:11] like GLM if I need to.
[00:55:14] All right.
[00:55:15] Auto billing it messed up last month,
[00:55:17] never doing it again. Okay, that's too
[00:55:19] bad. I will keep that in mind, probably
[00:55:21] not do that myself.
[00:55:25] Um use the Minimax subscription, gives
[00:55:27] good value for money. Okay, cool. Yeah.
[00:55:29] I don't know I probably like if I really
[00:55:32] want to scale this experiment, I don't
[00:55:33] think I can use any kind of subscription
[00:55:35] cuz I'll hit rate limits, but that's
[00:55:36] good to know.
[00:55:38] Cuz I might
[00:55:41] I use Minimax on Ollama, testing it now.
[00:55:43] Okay, that's very cool.
[00:55:45] Yeah, I mean I'm using a the biggest
[00:55:48] version of Minimax. I don't think that
[00:55:50] would really be realistically
[00:55:51] self-hosted. Like if I look up Minimax
[00:55:54] on Ollama,
[00:55:58] um yeah, they don't even offer you to
[00:55:59] install this yourself. It has to run
[00:56:01] through the cloud offering in Ollama.
[00:56:03] But I I believe if you look up like um
[00:56:07] there are self-hosted
[00:56:09] options. You must be running something
[00:56:11] self-hosted, right?
[00:56:13] If I just look up Minimax,
[00:56:15] um
[00:56:19] Oh yeah, so maybe you are running the
[00:56:20] biggest thing.
[00:56:23] Cuz you I guess there's like local
[00:56:25] options.
[00:56:27] This has got to be huge, though.
[00:56:31] Yeah, that's massive.
[00:56:34] 140 GB for the main thing. And then if I
[00:56:36] if we were to look at a
[00:56:39] Q4 quantization, oh wait, it's still 150
[00:56:41] GB. That doesn't seem right.
[00:56:44] But yeah, it's a 230 billion parameter
[00:56:46] model. I'm not running that on my
[00:56:48] computer, I'll tell you that.
[00:56:51] All right.
[00:56:52] Am I using local models for this? Nope,
[00:56:55] I'm using Minimax. Well, I mean you can
[00:56:57] host Minimax yourself, so it's an open
[00:56:59] source model, but I'm using it through
[00:57:01] the Minimax API.
[00:57:04] Uh thank you very much for the donation,
[00:57:06] Jared. Appreciate it a lot. Building a
[00:57:08] dark factory because even the machines
[00:57:10] refuse to work in light mode. Right.
[00:57:13] That's a good one. That's a very good
[00:57:14] one. And thank you for the donation, I
[00:57:16] appreciate it a lot.
[00:57:19] Um when using Arkon, is it needed to
[00:57:20] have bypass permissions for Claude Code?
[00:57:23] Uh yeah, cuz you're running the Claude
[00:57:25] agent SDK under the hood.
[00:57:28] You it's meant to be fire and forget,
[00:57:29] right? Like you're not supposed to
[00:57:30] babysit Arkon workflows. There's human
[00:57:33] in the loop built in, but that's a
[00:57:35] different thing. So I would use it.
[00:57:38] Like you can limit the permissions of
[00:57:39] Claude when Arkon runs through hooks.
[00:57:44] And if you really want to like create a
[00:57:45] settings.json to manage permissions
[00:57:47] there, you can do that as well.
[00:57:50] But uh yeah, usually I just do like YOLO
[00:57:52] mode when I'm running Arkon workflows
[00:57:54] and then I have like hooks that prevent
[00:57:56] reading from dot envs and removing
[00:57:57] directories and working outside of my
[00:58:00] designated codebase, like the work tree
[00:58:02] that Arkon creates.
[00:58:07] All right.
[00:58:10] Uh we have eight H100s, soon to get
[00:58:12] H200s. That is very very cool. I'm
[00:58:16] jealous. [laughter] I do not have an
[00:58:17] H100. Uh certainly not eight of them.
[00:58:20] That's awesome. Yeah, you're going to be
[00:58:22] able to run Minimax for sure. I think
[00:58:24] you could even run GLM.
[00:58:26] How big is GLM?
[00:58:28] I don't even know.
[00:58:31] Um
[00:58:33] Let's see.
[00:58:36] GLM is 744
[00:58:40] billion parameters.
[00:58:42] If you have eight H100s, though, I you
[00:58:44] would I think you'd be able to run.
[00:58:47] Can you run GLM 5.1 on eight H100s? I
[00:58:52] think you can.
[00:58:54] Like that should be decent. Yeah, cuz
[00:58:56] each one is 80 GB of VRAM. You're
[00:58:57] sitting pretty pretty there.
[00:59:01] Um I mean you might still need to
[00:59:02] quantize it potentially.
[00:59:08] 12.4
[00:59:09] tokens per second on HH eight H100s. So
[00:59:13] it's not like super super fast,
[00:59:16] but uh that's still very cool.
[00:59:19] I mean that's that's impressive.
[00:59:22] All right.
[00:59:24] I have not even a 100th of an H100.
[00:59:26] Same. Yep.
[00:59:27] >> [laughter]
[00:59:28] >> Those are expensive.
[00:59:30] Yeah, so yeah, 640 GB
[00:59:33] of VRAM. So yeah, you you I think you
[00:59:35] would definitely
[00:59:38] I mean, you'd want to probably quantize
[00:59:39] to get good results, but still insane.
[00:59:44] All right.
[00:59:46] Cool. So anyway, let's go back to our
[00:59:48] coding agent here
[00:59:50] because it came back with a summary.
[00:59:52] Okay.
[00:59:54] I've read the dark factory plan section
[00:59:56] 4.2 on triage specifically and the
[00:59:58] Archon workflow offering guide. Here's
[01:00:01] my proposal design for the dark factory
[01:00:03] triage before we build it. So our goal
[01:00:05] here, this is important for us to all
[01:00:07] understand,
[01:00:08] is to batch classify untriaged GitHub
[01:00:12] issues against the mission and factory.
[01:00:14] So these core files that guide the scope
[01:00:16] of work and things we're going to
[01:00:18] actually care about and things we won't.
[01:00:20] And then apply the labels and comments
[01:00:21] deterministically.
[01:00:23] So Claude makes the decision, or I
[01:00:26] should say Minimax makes the decision,
[01:00:28] but then we're going to have a
[01:00:29] deterministic steps in the workflow to
[01:00:31] automatically label and comment. Just to
[01:00:33] make sure that everything works the same
[01:00:34] way every time we run the triage.
[01:00:38] So we're going to run the orchestrator
[01:00:40] or runs when the orchestrator detects
[01:00:42] open issues with no factory label. So
[01:00:45] the orchestrator is the cron job. It
[01:00:47] runs every so often and when it sees
[01:00:49] that we have things that don't have a
[01:00:51] factory label, that means it's a new
[01:00:53] issue that our triage workflow hasn't
[01:00:56] looked at yet.
[01:00:57] So okay, we have five nodes.
[01:01:00] We're going to uh fetch the issues in
[01:01:02] parallel.
[01:01:04] Fetch the rules. So we're going to read
[01:01:05] in the mission and factory rules and
[01:01:07] then take a look at the pull request
[01:01:10] list cuz that'll also help us determine
[01:01:12] what is already in flight.
[01:01:15] Which this doesn't really make sense
[01:01:17] because I think we should be able to
[01:01:18] rely on the GitHub issues alone to
[01:01:20] figure out what's already in flight. But
[01:01:23] maybe this is just like a bit of an
[01:01:24] extra safety check, so I guess it
[01:01:26] doesn't really hurt to have it. But
[01:01:28] anyway, so layer one
[01:01:30] will do our classification. So it says
[01:01:32] Sonnet here, but remember we have it
[01:01:34] configured to route to Minimax when you
[01:01:36] we specify Opus Sonnet or Haiku in the
[01:01:39] Archon workflows. So it's going to
[01:01:41] classify each one of the issues and then
[01:01:43] we're going to have a bash step. So a
[01:01:45] deterministic step that will take in the
[01:01:48] JSON array of decisions that we have
[01:01:50] from the structured output from Claude
[01:01:52] code and we're going to loop over the
[01:01:55] JSON and then use the GitHub CLI
[01:01:56] deterministically to apply the labels
[01:01:58] and then also the comments to the issues
[01:02:00] as well.
[01:02:03] Okay, so we we have uh bash steps. So
[01:02:06] we're not using AI for layer zero as
[01:02:08] well, right? Like we just run the GitHub
[01:02:10] CLI
[01:02:11] to search through all the issues.
[01:02:13] We fetch the rules.
[01:02:17] Get the open pull requests. It says
[01:02:19] optional but useful.
[01:02:22] I mean, it's fine, but I guess we can
[01:02:24] keep it.
[01:02:26] And then classify
[01:02:28] the plan explicitly calls out scope
[01:02:30] judgment against a written mission
[01:02:31] requires nuance. Haiku often fumbles or
[01:02:34] in our case the high-speed Minimax would
[01:02:36] fumble. That makes sense. Cost is low
[01:02:38] since we run on less than 10 issues per
[01:02:40] batch in one call.
[01:02:42] Fair enough.
[01:02:44] Um okay, so
[01:02:48] you can see that one of the things we
[01:02:50] support in Archon workflows is defining
[01:02:53] the exact output that we require from
[01:02:55] the model. So this is like structured
[01:02:57] output with more classic agents if you
[01:02:58] guys have dealt with that before.
[01:03:01] But the point of this here is that when
[01:03:04] our coding agent goes through the
[01:03:05] classification process, we need a
[01:03:08] standard. I'm going to keep saying this
[01:03:10] throughout our livestream here.
[01:03:11] Everything is all about standards for
[01:03:12] reliability. We need a standard for the
[01:03:14] coding agent. It needs to communicate in
[01:03:16] the same way every single time um how
[01:03:19] we're going to label the issue.
[01:03:22] So it's going to output an issue number,
[01:03:24] the verdict, which is going to be either
[01:03:26] accept, reject, or needs human.
[01:03:28] It's right cuz need human it that's our
[01:03:30] fail-safe if it has failed to address
[01:03:32] the pull request multiple times.
[01:03:35] And the priority
[01:03:36] and then the classification, bug,
[01:03:38] feature, enhancement, chore, or docs.
[01:03:40] That's good enough for me.
[01:03:44] And then we have the prompt skeleton as
[01:03:45] well. So just telling it like when it
[01:03:48] goes through the classification what
[01:03:49] it's actually doing.
[01:03:51] Um and then what the script is the bash
[01:03:53] script is going to look like to actually
[01:03:55] invoke the GitHub CLI to label and
[01:03:57] comment on things.
[01:03:59] And then it's got some open questions as
[01:04:01] well.
[01:04:04] Um okay.
[01:04:06] So let's go ahead and answer these
[01:04:07] questions. So a batch size of 10 or
[01:04:10] five, let's do a batch of 10. And then
[01:04:13] help me understand like if we have
[01:04:14] actually opened up like 30 issues since
[01:04:16] last time the orchestrator ran, is it
[01:04:18] going to loop in Archon or what does
[01:04:20] that look like?
[01:04:22] And then should triage ever label
[01:04:24] without closing on reject?
[01:04:28] Plan says close rejected issues though
[01:04:30] with explanation.
[01:04:32] Um yes, we should definitely close
[01:04:34] issues when we reject them. Yep.
[01:04:37] Priority labels on need human. Currently
[01:04:38] I apply them. Useful so you can see at a
[01:04:40] glance which human review issues are
[01:04:42] urgent.
[01:04:45] Yeah, I think that they are definite
[01:04:47] definitely worth applying priority.
[01:04:50] Also help me understand how is this
[01:04:53] triage workflow
[01:04:55] going to know that we need a human,
[01:04:58] right? Cuz like we talked about in the
[01:04:59] plan how once the workflow or the pull
[01:05:02] request has failed twice on an issue,
[01:05:04] then we would say need human. So like
[01:05:07] what does that look like exactly?
[01:05:09] Okay. Man, these are some tough
[01:05:10] questions. Should I include a type star
[01:05:13] label or just lean on the existing
[01:05:15] GitHub issue labels? The plan doesn't
[01:05:17] mention type labels explicitly.
[01:05:19] I'd add them. Cheap signal for later
[01:05:21] filtering. Sure, yeah, we can add them
[01:05:22] and make sure you update the dark
[01:05:23] factory plan with that decision as well.
[01:05:27] Duplicate detection scope. Right now the
[01:05:29] classifier sees open PRs in current uh
[01:05:31] issue batch. Should it also see recently
[01:05:33] closed issues to catch repeat reports?
[01:05:36] Costs more context but catches more
[01:05:38] duplicates.
[01:05:40] Um I would say we don't really need this
[01:05:43] cuz if we rejected an issue before,
[01:05:44] we'll probably just reject it again. So
[01:05:46] we don't have to spend the context to
[01:05:47] look through recently closed issues.
[01:05:50] Um do mission.md and factory_rules.md
[01:05:52] exist in the target repo yet? The answer
[01:05:54] is yes. I did actually create them. They
[01:05:56] are on the main branch.
[01:05:58] Uh target repo path, which repo are we
[01:06:00] building this workflow into? The dark
[01:06:01] factory app repo, right? Not Dynamos
[01:06:04] engine. That is correct and actually I
[01:06:07] will give you the full path to the code
[01:06:09] base here at the start of the prompt.
[01:06:13] Okay.
[01:06:15] All right, woah, that's a mouthful.
[01:06:17] It asked a lot of questions, but okay,
[01:06:18] this is good. This is good cuz
[01:06:21] this is this is going to be a lot of
[01:06:23] work. We have our work cut out for us
[01:06:25] when we're building the system up front
[01:06:27] because every single assumption the
[01:06:29] coding agent makes is potentially going
[01:06:32] to be drastic when we're at this level
[01:06:35] of leverage creating our workflows and
[01:06:38] governance documents up front. Like we
[01:06:40] have to be very very intricate here. So
[01:06:43] I know that it can it can seem like I'm
[01:06:44] spending a lot of time on this, but man,
[01:06:47] this is important.
[01:06:48] Because if it doesn't understand how to
[01:06:50] label things right or it's not using
[01:06:52] GitHub issues in the way that I want it
[01:06:54] to, the whole system is going to fall
[01:06:56] apart. So I got to take time. I'm really
[01:06:58] glad that it's asking me a lot of
[01:07:00] clarifying questions here.
[01:07:03] All right.
[01:07:06] Cool.
[01:07:08] I'm still playing with Gemma 4 on my AMD
[01:07:10] 395 for local.
[01:07:13] Pretty cool. Yeah, Gemma 4 is good. Like
[01:07:15] it is legitimately a an impressive
[01:07:16] model.
[01:07:18] Uh it is I yeah, the one of the most
[01:07:20] popular ones right now on Ollama.
[01:07:24] Um ooh, I actually haven't heard of this
[01:07:26] one. Nemo strong cascade 2.
[01:07:30] That's cool. Man, there's so many models
[01:07:32] local models I want to try out right
[01:07:34] now.
[01:07:36] Um woah, the benchmarks actually look
[01:07:39] pretty good.
[01:07:41] Live code bench pro. It beats
[01:07:45] wow, it beats quant 3.5 397 billion.
[01:07:50] And it's almost as good as Kim K 2.5 a 1
[01:07:52] trillion parameter model. Seriously?
[01:07:56] That's kind of nuts.
[01:08:02] Interesting.
[01:08:05] Kind of want to try this one with the
[01:08:07] the dark factory.
[01:08:09] Okay, well anyway, I'm getting a little
[01:08:10] distracted here.
[01:08:13] All right. Yeah, that's exactly right.
[01:08:15] Quality work up front makes for some
[01:08:17] stellar loops and that is what I'm going
[01:08:19] for.
[01:08:21] All right, let's go back to Claude here.
[01:08:26] Okay, so let me address your two help me
[01:08:28] understand questions. No looping in the
[01:08:30] Archon workflow itself. The triage
[01:08:32] workflow is not a loop node. It's a
[01:08:33] one-shot DAG that processes a single
[01:08:35] batch and exit. Here's the actual flow.
[01:08:38] Okay, so if if we do have 30 issues
[01:08:40] opened in between orchestrator runs,
[01:08:43] orchestrator cycle one is going to fire
[01:08:45] triage workflows, process 10, and exit.
[01:08:47] Orchestrator cycle two sees work in the
[01:08:49] high priority lanes first. Only when
[01:08:51] those are empty does it fall through to
[01:08:53] the untriaged issues exist and run
[01:08:55] triage again. Okay.
[01:08:57] Uh so okay, this makes sense. So the 30
[01:08:59] issue spike does drain across three
[01:09:01] orchestrator cycles. So we do have to be
[01:09:04] careful
[01:09:07] because theoretically if there's like
[01:09:09] more than 10 issues and like created
[01:09:11] every single hour,
[01:09:13] then it is going to just kind of pile up
[01:09:16] and pile up. But I think this is
[01:09:17] actually okay because I don't want
[01:09:20] That would be unfortunate if there's
[01:09:21] more than 10 created every single hour.
[01:09:23] That's going to be so much work for it.
[01:09:26] Um
[01:09:27] Right.
[01:09:28] Okay.
[01:09:31] So, that makes sense. We can always
[01:09:32] change the limit if we want.
[01:09:34] How does triage know it to needs mark or
[01:09:37] it needs to mark needs human?
[01:09:40] You conflated two distinct escalations
[01:09:42] in the plan. I want to make sure we're
[01:09:43] on the same page cuz they're unrelated.
[01:09:45] Flow A is triage time needs human. When
[01:09:48] this workflow handles, the issue itself
[01:09:50] is problematic at intake. The classifier
[01:09:52] marks needs human when the issue is in
[01:09:53] scope but ambiguous,
[01:09:55] architecturally risky,
[01:09:57] a product judgment call,
[01:09:59] clearly the classifier's decision.
[01:10:04] Okay.
[01:10:08] I actually don't like that.
[01:10:10] I don't If I really want this to be a
[01:10:12] dark factory, I want it to either close
[01:10:15] issues or handle them. I don't want it
[01:10:17] to create this graveyard of issues that
[01:10:20] need my review when I'm not planning on
[01:10:22] actually reviewing them. So,
[01:10:24] Okay. I want to be clear here. I don't
[01:10:26] want to review issues unless there have
[01:10:29] been multiple failed attempts to address
[01:10:31] them. And so, for flow A, we should just
[01:10:34] close these issues with a comment. Like,
[01:10:37] if it's ambiguous or architecturally
[01:10:38] risky or whatever, let's just make a
[01:10:40] comment explaining that and then close
[01:10:42] the issue.
[01:10:45] Um and then I want you to check the code
[01:10:47] base itself to see if it has dot arcan.
[01:10:49] I believe it does.
[01:10:51] And then Okay, one design requirement I
[01:10:53] want your okay on. For the bash apply
[01:10:55] decisions node, I'm going to have to
[01:10:56] classify
[01:10:58] I'm going to have classify write its
[01:11:00] JSON output to the artifacts directory,
[01:11:02] makes sense, as a part of the prompt
[01:11:04] instructions, then I have apply
[01:11:05] decisions read the file with jq instead
[01:11:07] of relying on classify output
[01:11:09] substitution. The reason being the
[01:11:11] reason string will contain quotes,
[01:11:12] apostrophes, new lines, and emojis and
[01:11:14] arcons auto shell quoting um into a bash
[01:11:17] script is a foot gun waiting to happen.
[01:11:19] I mean, I guess. I don't Is that really
[01:11:22] not a problem? I'll have to look into
[01:11:23] that separately cuz that it might have
[01:11:25] just identified like a something we
[01:11:26] might want to fix in arcon. But anyway,
[01:11:28] writing to a file bypasses the whole
[01:11:30] quoting problem. It's one extra line in
[01:11:31] the prompt and a jq recursive in bash.
[01:11:34] Sound good. Uh sure, that sounds good
[01:11:37] for me.
[01:11:39] Okay, man, it's getting specific, but
[01:11:40] that's good. Like, I appreciate how in
[01:11:42] the weeds it is right now. That's That's
[01:11:44] what we need.
[01:11:47] All right. Cool. So, I think this is the
[01:11:49] last thing I need and then I can
[01:11:50] actually build the workflow.
[01:11:54] Cool.
[01:11:58] All right.
[01:12:01] What else we got in the chat?
[01:12:04] Thanks, man, for your shared work.
[01:12:06] You're very welcome. It is my pleasure.
[01:12:08] I love doing this stuff live with you
[01:12:10] guys. It's so fun. Just sharing
[01:12:12] everything.
[01:12:13] And you know, I was a little bit um I'm
[01:12:16] going to be honest, I was like a little
[01:12:16] bit hesitant to do this live stream
[01:12:19] because it's a bit slower than how I
[01:12:22] usually roll in my videos and live
[01:12:23] streams cuz I'm I'm building something
[01:12:25] live and I definitely at the stage where
[01:12:27] I'm taking something pretty slow.
[01:12:29] Like, we're not we're not going to have,
[01:12:31] you know, massive payoffs constantly
[01:12:34] here. Um it's a slow and steady right,
[01:12:36] it's a marathon, not a race. That's what
[01:12:38] it is when we're building a system like
[01:12:40] this up front.
[01:12:42] Okay.
[01:12:45] Um what now?
[01:12:50] That was a lot of uh information.
[01:12:53] Okay, confirm the execution plan.
[01:12:58] Okay, makes sense. Scaffold arcon, write
[01:13:01] the workflow,
[01:13:02] validate the workflow, fix any
[01:13:04] validation errors, and revalidate.
[01:13:06] This is great.
[01:13:08] Uh well, actually,
[01:13:10] yeah, I'll just say this is good.
[01:13:14] Go ahead. The other thing I was maybe
[01:13:15] going to ask it is like, what's its plan
[01:13:17] to actually invoke the workflow? Cuz
[01:13:20] when it does the arcon validate, that's
[01:13:21] just making sure the syntax is good. So,
[01:13:23] it's sort of like linting of the
[01:13:25] workflow. It's not going to run it yet
[01:13:26] and triage issues, but once it does the
[01:13:29] build, then I'll just have a
[01:13:30] conversation with it and ask it what its
[01:13:32] plan is to test it end to end.
[01:13:37] All right. Cool.
[01:13:39] I don't think we are too low on context.
[01:13:42] Yeah, we should be good for it to rip
[01:13:44] this whole thing. I wish I didn't only
[01:13:46] have 200,000 tokens, but oh well.
[01:13:50] All right.
[01:13:58] Cool.
[01:14:03] Can't wait till the Chinese firms use
[01:14:05] missile mythos outputs to train their
[01:14:07] models so open source local can really
[01:14:08] go stratospheric.
[01:14:11] Yeah, I mean, I'd be down for that.
[01:14:14] So, yeah, if they would use mythos for
[01:14:17] um
[01:14:18] synthetic data generation like they used
[01:14:20] opus, that that would be powerful.
[01:14:22] They're probably going to. Screw the
[01:14:24] lawsuits. They're probably just going to
[01:14:25] do it.
[01:14:26] >> [laughter]
[01:14:27] >> Yep.
[01:14:30] All right.
[01:14:32] Can I do a session on hermies? I assume
[01:14:35] you mean Hermes,
[01:14:37] like the new like kind of like open claw
[01:14:38] alternative.
[01:14:40] Um I would consider it. However, I'm
[01:14:43] more of a proponent of building your own
[01:14:45] second brain versus using something like
[01:14:47] Hermes or open claw.
[01:14:50] And you know what, while we're waiting
[01:14:51] for it to build the workflow here, I
[01:14:52] think this is a good time to chat about
[01:14:54] this quick. Let me actually um
[01:14:57] Hold on. Let me open up a page in my
[01:14:59] browser quick.
[01:15:04] I think this is the right link. Yeah,
[01:15:05] here we go.
[01:15:07] So, one of the really, really exciting
[01:15:09] things
[01:15:10] that I did quite recently in the
[01:15:13] dynamist community
[01:15:15] is I did a 4-hour boot camp
[01:15:18] teaching you how to build your own AI
[01:15:21] second brain from a scratch.
[01:15:23] And one of the things that I cover there
[01:15:25] is how you can take inspiration from
[01:15:27] tools like open claw or Hermes without
[01:15:29] having to build run it yourself.
[01:15:31] There are a lot of risks
[01:15:34] involved in running your own or in
[01:15:36] running a second brain that's not your
[01:15:39] own application. There's a lot of
[01:15:41] security problems with open claw and
[01:15:43] Hermes, not just in like vulnerabilities
[01:15:44] in the code base itself, but even just
[01:15:46] running something that you don't
[01:15:47] understand with permissions for your
[01:15:49] agent that you don't also don't truly
[01:15:51] understand.
[01:15:53] So, I'm a big proponent of building your
[01:15:55] own second brain from the ground up.
[01:15:57] And that's exactly what I cover in this
[01:15:59] course. And then I also edit it down
[01:16:01] into a more polished 3-hour version that
[01:16:04] still has like a lot of the good like
[01:16:05] Q&A in it. So, that's in the community
[01:16:07] as well as the third course for
[01:16:09] dynamist.
[01:16:10] So, if you're interested, like my second
[01:16:13] brain literally saves me 20 hours a
[01:16:15] week, like no exaggeration. It's crazy.
[01:16:17] Like, I've been running my business for
[01:16:19] about a year and a half now. Like, I
[01:16:20] know how long it takes for me to do a
[01:16:21] lot of these things that are like
[01:16:24] partially or fully automated for me now.
[01:16:26] And so, that's what I want for you as
[01:16:28] well. That's what I cover in the course.
[01:16:29] So, if that's if that sounds
[01:16:30] interesting, let me actually put a link
[01:16:31] to this in the chat for for YouTube
[01:16:34] quick.
[01:16:36] We've had a lot of people
[01:16:39] joining the community recently. It's
[01:16:41] very exciting for the second brain stuff
[01:16:43] and also because of arcon. Uh a lot of
[01:16:45] people are going to the course and
[01:16:46] they're sharing their second brain, like
[01:16:48] their own architecture and how they're
[01:16:49] molding it for their use cases cuz I one
[01:16:51] of the things I cover in the course is
[01:16:53] like, here's how you build the
[01:16:54] foundation of the second brain, but then
[01:16:56] I also talk about how you can, you know,
[01:16:58] guide it to help you build your own
[01:16:59] integrations and skills and other use
[01:17:01] cases that you have for it, even getting
[01:17:03] into it being like very proactive for
[01:17:05] you, anticipating your needs. So, yeah,
[01:17:08] people are sharing their own use cases
[01:17:09] and things. It's really cool to see.
[01:17:10] Like, I'm learning a lot from you guys
[01:17:13] even in the community itself. So,
[01:17:14] outside of just how I'm evolving it on
[01:17:16] my own. So, very, very cool. So, yeah,
[01:17:18] wanted to call it out really quick.
[01:17:20] Uh let's see where we are at with Claude
[01:17:23] now.
[01:17:25] Okay.
[01:17:28] Everyone wants to sell a course.
[01:17:30] Well, I mean,
[01:17:32] I provide a lot of value. I stand by
[01:17:34] what I what I provide there. So,
[01:17:37] yeah, I don't I don't really appreciate
[01:17:39] that the the cursing in the message
[01:17:41] there.
[01:17:43] Um but yeah, I mean, like I it
[01:17:45] seriously, there's a lot of value that I
[01:17:47] have and a lot of work I put into
[01:17:49] creating that boot camp.
[01:17:52] All right. Cool. So, anyway, here is
[01:17:55] what we've got for the workflow. It
[01:17:56] already built the whole thing. It's
[01:17:57] actually faster than I thought,
[01:17:58] honestly. But I guess we haven't really
[01:17:59] done any validation yet.
[01:18:02] Um let's see. So, we have our plan
[01:18:05] updated with the little bit of changes
[01:18:07] we made to the labeling system and the
[01:18:10] changes we made to our plan for the
[01:18:11] workflow.
[01:18:14] Um and then
[01:18:17] Okay, so we create the workflow itself.
[01:18:20] >> [sighs]
[01:18:20] >> Few implementation notes we're flagging.
[01:18:22] But I don't want to spend like too much
[01:18:24] time reading through this right now.
[01:18:30] Okay, I think that's fine. What's not
[01:18:33] done yet? Orchestrator agent.
[01:18:36] Fix GitHub issue adaptation. Okay. So,
[01:18:40] suggestion
[01:18:42] for next step. Before building the next
[01:18:44] workflow, I'd smoke test this one end to
[01:18:46] end. Create the labels in the repo,
[01:18:48] file one or two test issues,
[01:18:51] and um okay.
[01:18:55] That actually makes sense. But here
[01:18:56] here's the thing.
[01:18:58] Um I would love to smoke test, but I
[01:19:01] already have some issues that I have in
[01:19:04] the repository. So, maybe what we could
[01:19:06] do is we could run the workflow to
[01:19:08] triage those issues, but then just
[01:19:10] delete the labels after so we can bring
[01:19:12] us ourselves back to a blank slate. So,
[01:19:14] I want to do the full test, but I I want
[01:19:17] to like get it back to the original
[01:19:18] state before I did my testing, if that
[01:19:21] makes sense.
[01:19:22] Uh but you can feel free to like iterate
[01:19:24] on the workflow and everything before
[01:19:25] you go back to the blank slate.
[01:19:28] Okay.
[01:19:30] So, yeah, I wanted to like actually run
[01:19:32] it, but not like leave a mess of of
[01:19:34] triaging and stuff. Cuz this repo that I
[01:19:36] have right here, like I want to keep it
[01:19:38] pure, right? For like when I actually
[01:19:40] kick off the dark factory, like have all
[01:19:43] the workflows built.
[01:19:45] Okay. And then someone asked for me to
[01:19:47] share the link for what I had open up in
[01:19:48] Chrome. This is the link right here.
[01:19:51] Um cool.
[01:19:53] All right. Thanks, Cole. This is
[01:19:54] awesome. I appreciate it a lot. Thank
[01:19:55] you very much. Thanks, Cole. Will join
[01:19:57] Dynamis.
[01:19:59] Thank you. I appreciate it a lot. Yeah,
[01:20:00] I'll be happy to have you in the
[01:20:01] community. Watching at 5:20 a.m. from
[01:20:05] New Zealand. Well, thank you for tuning
[01:20:07] in so early. I appreciate that a lot.
[01:20:10] Cool.
[01:20:12] All right.
[01:20:15] Let's see.
[01:20:19] I I know it's a reference to shooting
[01:20:20] yourself in the foot, but I've never
[01:20:22] heard the term foot gun. Am I alone?
[01:20:24] Actually, honestly, Chris, that's a good
[01:20:26] point. So, that's in reference to what
[01:20:28] Claude mentioned earlier.
[01:20:31] Uh I guess I haven't heard foot gun,
[01:20:32] either.
[01:20:34] I don't know. Yeah, I've heard I've
[01:20:35] heard shooting yourself in the foot a
[01:20:36] million times. I use that expression
[01:20:38] myself a lot, but yeah, I guess that's
[01:20:40] just a shorter way to put it.
[01:20:45] Cool.
[01:20:48] All right.
[01:20:51] Uh I definitely want to join Dynamis,
[01:20:53] but just bought a house. Fair enough.
[01:20:54] Well, congratulations, Stuart, on your
[01:20:56] new home. While I'm trying to get
[01:20:58] everything operating free and local for
[01:21:00] a first run. Then once I have output, I
[01:21:02] can pay for upgrades. Sounds good. Yeah,
[01:21:05] fair enough. Yeah, congrats on the
[01:21:06] house. That's exciting.
[01:21:08] You're joining as well? Very cool. I
[01:21:10] appreciate it. Welcome to the Dynamis
[01:21:12] community.
[01:21:14] Thanks, Cole. This is super cool. I
[01:21:16] appreciate it a lot. Yeah, I I
[01:21:17] appreciate you guys uh finding interest
[01:21:19] in something where it's like a little
[01:21:21] bit slower pace as I have to like really
[01:21:23] spend my time ideating and and building
[01:21:25] the system up front.
[01:21:27] So, yeah, happy to to build this in in
[01:21:29] public, so to speak.
[01:21:32] All right. Cool. So,
[01:21:35] let's see. The workflow is currently in
[01:21:37] progress.
[01:21:41] Looks good.
[01:21:42] Um you know what I I kind of want to do,
[01:21:44] cuz I'm running this workflow for the
[01:21:45] first time, is I would love to uh view
[01:21:48] the logs in the Archon UI.
[01:21:53] So, let me actually ask it. I I don't
[01:21:54] have it started I restarted my computer
[01:21:56] recently, so I don't have it up and
[01:21:57] running.
[01:21:58] Start the back end and front end of
[01:21:59] Archon.
[01:22:01] This is how easy it is, by the way. You
[01:22:03] don't You don't even have to run the
[01:22:03] commands in the terminal or run the
[01:22:05] containers or anything yourself. You
[01:22:06] just let it go.
[01:22:09] So, we'll take a look.
[01:22:13] Okay.
[01:22:14] I mean, bun run dev's not hard to
[01:22:16] remember, but I just like doing that.
[01:22:18] >> [laughter]
[01:22:19] >> All right. So, let's head on over to
[01:22:21] Archon.
[01:22:25] Go to the dashboard.
[01:22:29] Um it looks like the back end is still
[01:22:31] starting.
[01:22:34] Can you monitor the back end and let me
[01:22:36] know if it's failing to start?
[01:22:38] Not sure. I might be on a wrong branch
[01:22:40] or something. Oh, no. Okay, I think
[01:22:42] Wait, hold on.
[01:22:48] Um
[01:22:50] Why is my workflow not showing? I have
[01:22:51] these uh
[01:22:52] These workflows from way back in the
[01:22:54] Saturday live stream that I forgot to
[01:22:55] continue are still running. That's
[01:22:56] funny. So, they're still paused, but
[01:22:58] it's not showing up.
[01:23:01] Where did it
[01:23:02] Is it done running already?
[01:23:07] Oh, okay. It did actually finish.
[01:23:10] Huge win and a Windows bug. Let me break
[01:23:12] down what happened. All three parallel
[01:23:13] fetch nodes finished. Classifier ran in
[01:23:15] 30 seconds. Decision.json was written
[01:23:17] successfully.
[01:23:20] The fetch open PRs node paid for itself
[01:23:22] immediately. It thought that the
[01:23:23] classifiers would have accepted seven
[01:23:24] issues that are already being worked.
[01:23:25] What broke is the JQ uh failed on Git
[01:23:29] Bash for Windows. Oh, that makes sense.
[01:23:32] Yeah. Okay, so let's see.
[01:23:34] Okay, so it's figuring out how to fix
[01:23:35] here.
[01:23:37] Caught another bug.
[01:23:39] Okay. Now it's running the workflow
[01:23:42] again.
[01:23:44] It's cool that it's iterating. Like
[01:23:45] little little blips that it's finding,
[01:23:47] but like I mean, as long as it's able to
[01:23:49] iterate, I'm happy with it. Um yeah,
[01:23:51] okay, there we go. So, now we can see
[01:23:53] the workflow. It's not running, but the
[01:23:55] one that just failed, it uh shows up
[01:23:57] here.
[01:23:58] So, you can take a look at the logs uh
[01:24:00] from the failure.
[01:24:02] So, yeah, everything is working as
[01:24:04] intended in the Archon web UI. We just
[01:24:06] need to fix the syntax for the the
[01:24:09] underlying workflow itself.
[01:24:11] Cool. So, all right. Oh, now it's
[01:24:14] running again. Okay, very good. View the
[01:24:15] logs. Very cool.
[01:24:17] Looking good. All right.
[01:24:20] We'll see if it works this time.
[01:24:25] All right.
[01:24:28] Till foot gun means that. Yep, today I
[01:24:30] learned as well.
[01:24:34] Eric said the courses in Dynamis are
[01:24:36] standing. I'm a career dev and seen a
[01:24:37] lot of courses. Dynamis courses are
[01:24:39] exceptional. Yeah, I appreciate it very
[01:24:41] much. I I appreciate you guys like
[01:24:43] sharing that, especially after someone
[01:24:45] comes in and just like has to say
[01:24:47] something mean for no reason.
[01:24:49] Which I mean, I got thick skin. Like
[01:24:50] it's fine. I I understand. And And by
[01:24:52] the way, like to to that person who who
[01:24:56] was a little mean, like I do get it.
[01:24:58] Like I understand that like everyone is
[01:25:00] just trying to sell a course.
[01:25:02] Uh and and I can see how it just feels
[01:25:04] like I'm just fitting in with that
[01:25:05] crowd. Like I I get it. It's okay. I'm
[01:25:07] not just like living in a bubble where I
[01:25:08] I think that you're saying it totally
[01:25:10] out of pocket. Like I understand. But
[01:25:11] like at the same time, like I really do
[01:25:14] believe that I'm not I'm it's not saying
[01:25:16] I'm expecting you to do this, but like
[01:25:17] if you were to actually go through the
[01:25:19] second brain course, I I feel like you
[01:25:21] would take back what you said. Like
[01:25:22] honestly, I'm just going to say that.
[01:25:24] Um but yeah, not not like I'm thinking
[01:25:26] I'm going to change your mind or
[01:25:27] anything.
[01:25:29] Yeah.
[01:25:32] All right.
[01:25:33] Having never built anything before, but
[01:25:35] amazed how easy this is to learn if you
[01:25:37] think logically.
[01:25:38] That's right. Yeah. And even just like
[01:25:40] slowing down and using Claude code to
[01:25:43] help you think logically. Like break it
[01:25:46] down for me step by step. Or like help
[01:25:48] me plan this and ask me questions. Like
[01:25:51] those kinds of things are are uh how you
[01:25:53] get the most out of Claude code.
[01:25:56] Because it it can
[01:25:59] I mean, like large language models make
[01:26:00] mistakes. They're never going to be
[01:26:01] perfect, and that's why you need to
[01:26:03] align with them. But you can have them
[01:26:05] walk you through the alignment process,
[01:26:08] cuz they do a really good job at that.
[01:26:11] Okay.
[01:26:12] Uh cool. So, it looks like it ran end to
[01:26:15] end, and it actually closed a lot of
[01:26:17] issues here. So, three were accepted,
[01:26:19] and then seven were rejected. Okay,
[01:26:21] interesting.
[01:26:22] Uh well, I'm curious to dive into that
[01:26:24] now.
[01:26:26] It says that it's still waiting here.
[01:26:30] Cool. Smoke dev said as a part as part
[01:26:33] of as a student of the course, I agree.
[01:26:35] Dynamis is an absolute game changer for
[01:26:36] me. Lots of value. I appreciate it a
[01:26:38] lot. Thank you very much.
[01:26:41] Uh
[01:26:42] All right.
[01:26:44] Cool. So,
[01:26:45] uh looks like it is done.
[01:26:51] Cool. And that was fast, by the way. It
[01:26:53] didn't take that long.
[01:26:55] Now, we we didn't run this workflow with
[01:26:57] Minimax. Let me be clear, cuz we didn't
[01:26:59] run this on the VPS yet. But we will get
[01:27:01] there. We're just testing it right now
[01:27:02] locally. In fact, I should probably test
[01:27:05] my or check my Anthropic rate limit.
[01:27:08] Uh oh, it's not even that bad. Okay,
[01:27:10] we're good.
[01:27:11] Here, I'll even share that on my screen
[01:27:13] here.
[01:27:14] Let me duplicate
[01:27:18] and bring it over.
[01:27:20] So, this is my limits right now.
[01:27:22] Uh look at that. We've only We've
[01:27:24] literally only used 10% so far. So, not
[01:27:26] bad, especially without bad the rate
[01:27:28] limits are. Um
[01:27:31] Wait, what is this? Daily included
[01:27:33] routine runs? This is new, like as of
[01:27:37] just today.
[01:27:38] Included routine runs per rolling 24
[01:27:41] hours. I actually This This is weird.
[01:27:43] I've never seen this in the usage page
[01:27:45] before from the Claude app.
[01:27:48] And yeah, my weekly limit, I'm at
[01:27:49] already at 50%, and it resets on Friday.
[01:27:52] And over the past couple days, I've been
[01:27:54] doing so much testing with Minimax that
[01:27:56] I haven't even been using my Anthropic
[01:27:57] that much. Like it's crazy. I I got to
[01:27:59] like 40% over the weekend.
[01:28:02] Yeah.
[01:28:04] Okay. So, anyway, I was going to look at
[01:28:06] the classifications that it did here.
[01:28:11] Oh, it already undid everything.
[01:28:13] Shoot. So, I can't actually see
[01:28:16] cuz it deleted the comments.
[01:28:21] Okay, so this is one of the ones that
[01:28:22] was accepted. So, we can see that the
[01:28:24] labels are removed, cuz I asked it to
[01:28:26] undo things after it's testing. But we
[01:28:29] can see that from the history here that
[01:28:31] like this one, it added the factory
[01:28:33] accepted with a priority low.
[01:28:35] If we look at um I don't know, one that
[01:28:38] it rejected here.
[01:28:41] Where is this one? This one, it added
[01:28:44] factory rejected. Closes not planned. It
[01:28:47] had it it an issue comment here at one
[01:28:49] point. That's another thing that it
[01:28:50] cleaned up. So, I honestly kind of wish
[01:28:52] that it did the cleanup after I told it
[01:28:53] to, but that's my fault, because I told
[01:28:55] it to do the cleanup immediately after.
[01:28:59] We can see here that um it has taken
[01:29:01] care of all the cleanup.
[01:29:03] All 11 issues are back open with zero
[01:29:05] labels. But anyway, the workflow
[01:29:07] actually worked extremely well.
[01:29:10] Um okay.
[01:29:12] What it did not touch. Yeah, that makes
[01:29:15] sense. Ready for the next step. The
[01:29:16] triage workflow is committable. Next
[01:29:18] logical builds per the plan.
[01:29:20] Uh get help label one-time setup for the
[01:29:22] real run. Already done implicitly.
[01:29:25] Dark Factory validate PR.
[01:29:29] Well, it shouldn't the next step be to
[01:29:30] create an adaptation of the Archon
[01:29:32] GitHub issue fix workflow for the Dark
[01:29:34] Factory.
[01:29:36] Cuz I I think like I don't know why it
[01:29:38] The plan wasn't really clear on like we
[01:29:41] got to actually build something for
[01:29:42] implementing the pull requests, not just
[01:29:44] validating and fixing the issues that
[01:29:46] come up. So, I'm going to try to point
[01:29:47] it in the right direction here.
[01:29:49] Um cuz I want I think that'd be the next
[01:29:50] workflow to work on. So, we have the
[01:29:53] triage, which is going to figure out
[01:29:54] what issues do we actually want to
[01:29:56] address, and then in parallel we'll
[01:29:57] invoke the Archon workflows to
[01:30:00] you know, take it from issue to pull
[01:30:02] request.
[01:30:05] Okay.
[01:30:06] You're right, and I missed that. Of
[01:30:08] course, Claude has to be sycophantic and
[01:30:10] tell me that I'm right.
[01:30:12] Um but I am.
[01:30:14] The triage workflow will produce his
[01:30:15] labels, but those labels are inert until
[01:30:18] there's a working fix workflow that
[01:30:19] knows how to validate.
[01:30:21] Uh the plan calls this out implicitly as
[01:30:23] a hard blocker. The moment a bug fix or
[01:30:24] feature lands the default bun run
[01:30:27] validate will still blow up on Python
[01:30:28] syntax. Right. So, this this is a little
[01:30:31] bit behind-the-scenes planning I was
[01:30:33] doing. Basically, the fix GitHub issue
[01:30:35] work
[01:30:35] get fix GitHub issue workflow built into
[01:30:38] Archon isn't quite specific enough for
[01:30:40] my code base. So, I just need to take
[01:30:43] this as an example. This is one of the
[01:30:45] workflows that ships by default with
[01:30:46] Archon, and I just need to tweak it to
[01:30:49] work a little bit better with my Dark
[01:30:51] Factory specifically.
[01:30:54] So, it's going to do some research for
[01:30:56] me. So, understand the structure of the
[01:30:57] repo,
[01:30:58] um understand the command or the
[01:31:00] workflow that we're going to adapt, and
[01:31:02] then see what we have for our global
[01:31:03] rules already.
[01:31:05] All right.
[01:31:10] Let's see.
[01:31:14] All right. Yeah, I appreciate it. Don't
[01:31:17] care for such comments. You're really
[01:31:18] delivering a lot of value for free as
[01:31:19] well. I think we all value that a lot.
[01:31:22] Yeah, I appreciate that. And um even
[01:31:24] when I do have the community as a you
[01:31:26] know, paid thing, I I do try to give an
[01:31:28] insane amount uh for free.
[01:31:31] Like what I'm doing right now. So, I
[01:31:32] appreciate you recognizing that. And
[01:31:34] that really is important to me. Like no
[01:31:35] matter what, I always want to just be
[01:31:37] constantly giving. That's also why
[01:31:39] Archon is fully open source. This
[01:31:41] repository has nothing hidden. I mean,
[01:31:44] the Dynamis community had early access
[01:31:46] to it and got to even help shape some of
[01:31:48] the direction for it. And that's one of
[01:31:50] the cool parts of having a community. Uh
[01:31:52] but it's it's for everyone. That's
[01:31:54] That's always been the goal.
[01:31:58] All right.
[01:31:59] Is there a link for the community? Uh
[01:32:01] yeah, yeah. Sorry, I'll I'll send this
[01:32:03] again here in the chat.
[01:32:05] Um so, this this is a link to kind of
[01:32:08] like the page like showcasing the AI
[01:32:10] second brain, but you just scroll down
[01:32:12] and there's a lot of buttons here to
[01:32:14] join.
[01:32:15] So, yeah. I appreciate that.
[01:32:17] All right.
[01:32:19] Let's go Sorry, I'll I'll watch the logs
[01:32:21] here.
[01:32:22] All right.
[01:32:26] See, a strong DM depends on a digital
[01:32:28] twin universe, which creates behavioral
[01:32:30] clones of external services like Okta,
[01:32:34] Jira, Slack to allow agents to run
[01:32:35] thousands of realistic tests.
[01:32:38] Yeah. Okay, if you really get into
[01:32:40] StrongDM setup, it is quite impressive.
[01:32:43] So, it certainly won't be uh building
[01:32:45] everything StrongDM has, at least for
[01:32:48] now. But also, my application is luckily
[01:32:50] a lot simpler, where I won't necessarily
[01:32:52] need to to have the same level of depth.
[01:32:56] Right? Like simpler application means I
[01:32:58] don't have to go as deep, but I still
[01:32:59] get like the same reliability like they
[01:33:01] built. Uh but yeah, if you want to like
[01:33:03] really read into what StrongDM has
[01:33:05] built, again, they haven't open sourced
[01:33:07] their Dark Factory. But they've, you
[01:33:09] know, open sourced the PRD like I showed
[01:33:12] at the start of the stream. And then I
[01:33:14] think they have like some blog posts as
[01:33:15] well where they break down a lot of what
[01:33:17] their architecture looks like.
[01:33:19] It's pretty cool. It's It's really
[01:33:21] inspirational.
[01:33:25] All right.
[01:33:27] Cool.
[01:33:30] Um routine runs. Is that analogous to
[01:33:32] OpenClaw crons?
[01:33:34] I mean, probably analogous to some kind
[01:33:37] of cron job. I don't know exactly. Like
[01:33:40] this I've checked my Anthropic usage
[01:33:42] every single day cuz I don't want to be
[01:33:44] on top of especially the 5-hour rate
[01:33:46] limit. This This I literally like wasn't
[01:33:49] This wasn't there this morning.
[01:33:50] Um so, yeah. I don't I don't know what
[01:33:52] it is exactly. Maybe Maybe they have
[01:33:54] something If I just like search Claude
[01:33:56] code routine runs.
[01:34:00] Okay.
[01:34:02] Um oh yeah, here we go. 47 minutes ago,
[01:34:05] we have a post
[01:34:06] on the Claude code subreddit. New Now in
[01:34:09] research preview, routines in Claude.
[01:34:11] Configure a routine once, a prompt, a
[01:34:14] repo, your connectors, and it can run on
[01:34:16] a schedule.
[01:34:17] Scheduled routines let you give Claude a
[01:34:19] cadence and walk away.
[01:34:22] Um okay, I was just about to say, they
[01:34:24] already have the slash schedule in the
[01:34:26] CLI. If you've been using slash schedule
[01:34:28] in the CLI, those are routines now.
[01:34:30] There's nothing to migrate. Okay, that
[01:34:32] makes sense. So, they're they're taking
[01:34:33] something that was has already been
[01:34:34] there, but now they're just building it
[01:34:36] into other platforms. Like I I assume
[01:34:38] that like slash schedule used to be an
[01:34:40] only CLI thing, and now it's like within
[01:34:42] Claude desktop and co-work and the
[01:34:44] Claude app.
[01:34:46] I guess that's what it is. I I mean,
[01:34:47] it's pretty cool. So, yeah, literally it
[01:34:49] is cron jobs. Just being able to run
[01:34:50] something that runs every hour
[01:34:52] or day or whatever.
[01:34:55] That's pretty cool.
[01:34:58] All right. They are always shipping. It
[01:35:01] is crazy.
[01:35:03] But good for them.
[01:35:05] Okay. Very cool. So, now
[01:35:08] uh okay, how long have we been streaming
[01:35:10] for?
[01:35:11] Um we've been streaming for a little
[01:35:13] over an hour and a half. Okay, so I am
[01:35:15] able to stream for Wait, I got to check
[01:35:17] my calendar. I'm able to stream for 2
[01:35:19] and 1/2 hours. And I'm I'm loving what
[01:35:22] we're building right now. So, I'm
[01:35:23] thinking I'm going to go till Yeah, I'm
[01:35:25] planning on streaming till 1:30
[01:35:28] Central Time. So, like another hour
[01:35:29] here.
[01:35:30] We'll see how far I get
[01:35:32] with all of our workflows.
[01:35:35] Okay.
[01:35:37] Shh. What are we doing here? Okay. Wow,
[01:35:40] there's there's so much output. I'm
[01:35:42] getting a little like
[01:35:44] um burnt out on the like burnt out from
[01:35:47] all of Claude's output here. It's a lot
[01:35:48] to parse through cuz it's kind of it's
[01:35:51] fairly complex what we're working on
[01:35:52] right now, I will say.
[01:35:56] Okay.
[01:35:57] Reg YouTube chat's validation story is
[01:35:59] prescribed, but not wired. Okay.
[01:36:03] Uh global rules prescribe the exact
[01:36:05] commands, but none of those dev steps
[01:36:06] are actually installed yet.
[01:36:09] No tests, no makefile, no CI. Right.
[01:36:11] Yeah, I haven't built that yet.
[01:36:15] The factory should add these when the
[01:36:16] first PR touches them. I don't actually
[01:36:18] agree with that. I want to build that
[01:36:19] ahead of time.
[01:36:21] I [laughter] love this. It's cute, but
[01:36:23] it creates a chicken and egg problem.
[01:36:25] Oh, that's funny. I Wow, Claude Claude
[01:36:28] has some personality now, I will say.
[01:36:32] Uh and yeah, I agree with Claude here
[01:36:34] that that is a bad decision to put in
[01:36:36] the global rules.
[01:36:37] Um okay.
[01:36:39] The bundled Archon fix GitHub issue
[01:36:41] workflow is mostly language agnostic.
[01:36:44] That makes sense. So, my surgical fix is
[01:36:45] just one file.
[01:36:47] My recommendation is option B, custom
[01:36:49] command override.
[01:36:53] Uh here's why. Okay. All right. Yeah,
[01:36:56] sure.
[01:36:58] Full workflow fork.
[01:37:02] All right.
[01:37:07] You know, so it's saying I don't need to
[01:37:09] create a workflow from scratch, and I
[01:37:11] can just use what I have as the bundled
[01:37:13] workflow.
[01:37:15] Um
[01:37:18] Yeah. Okay.
[01:37:19] Yes, you're right. We definitely want to
[01:37:21] bootstrap the development dependencies
[01:37:23] manually.
[01:37:25] And then I actually do want to create a
[01:37:27] custom workflow entirely.
[01:37:30] So, yes, I know that there's not much we
[01:37:32] have to change from the GitHub issue fix
[01:37:33] workflow, but I want to be able to
[01:37:35] evolve it separately from the default
[01:37:37] Archon workflow anyway. So, we can
[01:37:38] mostly copy it and then obviously just
[01:37:40] changing the validate command, but yeah,
[01:37:42] let's go ahead and and do it that way.
[01:37:44] Um
[01:37:47] Yeah.
[01:37:50] And then sure, we can we can smoke test
[01:37:52] issue number 26 after.
[01:37:55] Okay.
[01:37:56] There we go.
[01:37:57] Um oh crap, we have to run the
[01:37:59] compaction now. Oh, I forgot about that.
[01:38:01] I probably should have just worked on
[01:38:02] the workflow in a separate conversation.
[01:38:05] Um cuz now that it does a memory
[01:38:06] compaction, it has to reload its skills
[01:38:09] and stuff. So,
[01:38:10] All right. Now that you just did a
[01:38:11] memory compaction, I need you to uh read
[01:38:14] the Dark Factory plan again.
[01:38:16] And then load the Archon skill. Just to
[01:38:18] make sure you have full context before
[01:38:19] you go into building the second workflow
[01:38:21] and um doing the smoke test on issue
[01:38:24] number 26.
[01:38:26] Make sure you build this workflow from
[01:38:28] scratch. And then uh also, I want to use
[01:38:31] the commands folder for all Archon Dark
[01:38:33] Factory workflows. So, make sure we
[01:38:35] don't have inline prompts for the other
[01:38:38] the triage workflow we just built as
[01:38:40] well.
[01:38:41] Um so, that's a little specific, but I
[01:38:43] just realized that um I wanted to
[01:38:45] organize my workflows a bit better than
[01:38:46] I did up front if I go do the code base
[01:38:49] now.
[01:38:50] We have the Dark Factory triage.
[01:38:52] Um this prompt is inline, and it's
[01:38:55] massive.
[01:38:56] So, I would rather extract this to a
[01:38:59] command.
[01:39:00] Right, we don't have any commands right
[01:39:02] now, but in Archon, your workflows can
[01:39:04] reference a command, which is just like
[01:39:06] a separate markdown document. Just to
[01:39:08] have a better way to organize things, so
[01:39:09] we don't have have massive ugly prompts
[01:39:11] in line in the workflow itself.
[01:39:14] I might even want to do the same for
[01:39:16] this. This apply decisions bash is like
[01:39:19] really long.
[01:39:22] Yeah,
[01:39:23] there's there's a lot of optimizations
[01:39:25] that I can make. Just for the sake of
[01:39:27] the live stream, I am moving decently
[01:39:29] quickly.
[01:39:31] So certainly will be iterating on things
[01:39:32] off camera
[01:39:34] like before I make the YouTube video
[01:39:36] tomorrow that kind of like you know sums
[01:39:37] everything up for the dark factory that
[01:39:39] I'm working on.
[01:39:44] All right.
[01:39:49] Cool.
[01:39:51] I appreciate it. Haters going to hate.
[01:39:52] Dynamis rocks and the value of your
[01:39:54] contributions Cole are frankly
[01:39:56] incalculable. I appreciate it a lot.
[01:39:58] That means a lot.
[01:40:00] Price of Dynamis is a lot more
[01:40:01] reasonable than most of the courses
[01:40:03] community subscriptions being offered. A
[01:40:04] lot of them sound like snake oil.
[01:40:06] Get rich quick for thousands of dollars.
[01:40:09] Yeah, there there unfortunately is a lot
[01:40:11] of that out there.
[01:40:12] There there's one
[01:40:14] sort of YouTuber in particular that I
[01:40:17] don't want to call out exactly
[01:40:20] or like name drop, but he he's a
[01:40:23] respectable guy. He does a lot around
[01:40:25] second brains specifically like even
[01:40:27] before generative AI. A lot of you might
[01:40:29] know who I'm talking about.
[01:40:31] So I'm not saying the course is going to
[01:40:33] be bad, but he like he's like running
[01:40:35] these cohorts for building your own
[01:40:37] second brain.
[01:40:39] And he's charging $2,000 for it. It's
[01:40:42] like
[01:40:43] crazy. Like what? Like $2,000 just to
[01:40:46] like learn how to build a second brain.
[01:40:47] Like I taught that for
[01:40:49] in a 4-hour workshop and you can just
[01:40:51] join the community for it. Like
[01:40:54] it's not $2,000.
[01:40:56] >> [laughter]
[01:40:56] >> Yeah.
[01:40:57] Anyway, there there are some pretty
[01:40:59] expensive things out there for sure.
[01:41:03] All right.
[01:41:04] Will the dark factory repo be open
[01:41:06] source after the live? So not fully
[01:41:10] but it'll be within like the next couple
[01:41:12] of weeks I will open source it. So I
[01:41:14] need some more time to validate and
[01:41:16] really polish things, but the plan is to
[01:41:18] make it public by the end of the month.
[01:41:19] Like everything public where you can
[01:41:21] even open an issue and have it work on
[01:41:23] it for you.
[01:41:24] So
[01:41:27] Who could I be talking about?
[01:41:29] Yeah, yeah you got some of you guys
[01:41:31] know. Some of you guys know. And and
[01:41:32] again I respect him. Well, I guess I
[01:41:35] would say I have more of a neutral
[01:41:36] opinion. I haven't gotten like too deep
[01:41:37] into his stuff. So I'm not like trying
[01:41:39] to dunk on him or anything. I'm just
[01:41:40] saying that like to me like $2,000 to
[01:41:42] join a cohort is a little ridiculous,
[01:41:44] but
[01:41:45] to each their own. I mean some some
[01:41:47] people
[01:41:48] definitely
[01:41:49] value having that kind of like cohort
[01:41:53] style.
[01:41:54] It's yeah, to each their own.
[01:41:57] All right.
[01:42:00] Okay, let's see here. What else we got?
[01:42:04] The old you're absolutely correct. Yeah,
[01:42:06] that's right.
[01:42:08] All right.
[01:42:10] Bit out of context, but
[01:42:13] could we build a skill to make Claude
[01:42:15] code and and anti-gravity interoperable?
[01:42:19] You definitely could. Like if you wanted
[01:42:22] anti-gravity to invoke Claude like in
[01:42:24] headless mode, you could if you wanted
[01:42:26] to.
[01:42:27] I think I don't know [snorts] if
[01:42:29] anti-gravity has like a CLI, but Gemini
[01:42:32] has a CLI obviously. So
[01:42:35] you could have them invoke each other.
[01:42:38] So you could like have a workflow where
[01:42:40] it's like Claude implements the code and
[01:42:42] then it calls the Gemini CLI to do the
[01:42:44] validation. Like you could do that kind
[01:42:46] of thing 100%. Like that's something
[01:42:48] that I actually want to build like
[01:42:49] directly in the into Archon workflows.
[01:42:51] Like being able to have different
[01:42:52] providers at different nodes for
[01:42:54] planning and implementation and
[01:42:55] reviewing.
[01:42:59] All right.
[01:43:02] Okay, this is really interesting.
[01:43:03] MiniMax with open code performs much
[01:43:05] faster and better than in Claude code.
[01:43:08] Probably the context blow of all the
[01:43:09] prompting that goes under the hood in
[01:43:11] Claude code.
[01:43:12] So that Okay, that's good to know cuz
[01:43:14] yeah, maybe I would want to change this
[01:43:16] harness to use like Pi or open code
[01:43:19] instead.
[01:43:20] Okay.
[01:43:22] I I will have to look into that. Like I
[01:43:24] said, there's so many ways that I can
[01:43:25] probably improve this harness
[01:43:27] with the prompting and how I organize
[01:43:29] the workflows and my mission document
[01:43:31] and my factory rules and even just the
[01:43:34] tool that I'm using under the hood. Like
[01:43:36] maybe I do want to use Pi or open code
[01:43:37] instead.
[01:43:41] All right.
[01:43:45] Let's see.
[01:43:47] One way to find out if the course or
[01:43:49] subscription you paid for justify the
[01:43:51] cost is if you ship a product that
[01:43:52] others paid for to recoup that cost. I
[01:43:55] mean yeah, exactly.
[01:43:57] That right cuz then then it's like
[01:44:00] there's no argument there. Like if you
[01:44:01] made more money thanks to what you
[01:44:03] learned there
[01:44:04] and you built something from it then
[01:44:06] yeah, pays dividends. Exactly right.
[01:44:12] All right.
[01:44:18] Why does it feel like we've been here
[01:44:19] for 1 plus hours and not achieved much?
[01:44:22] I mean that's something that I've been
[01:44:23] trying to be very transparent about here
[01:44:25] is that like we're spending a lot of
[01:44:26] time planning and defining the
[01:44:28] architecture and the system for the dark
[01:44:30] factory up front. And it it has to take
[01:44:33] time. It it has to. I can't rush it. And
[01:44:36] and to be honest like I would probably
[01:44:37] be going even slower
[01:44:39] if I wasn't in a live stream here
[01:44:41] because in the end like if I want this
[01:44:44] thing to rip through issues really
[01:44:45] quickly, if I want the dark factory to
[01:44:47] be self-sustaining and really efficient
[01:44:49] and reliable, I have to be slow up
[01:44:52] front. That's what I'm and that's kind
[01:44:53] of the the teaching lesson here honestly
[01:44:55] as well.
[01:44:57] So
[01:44:59] Yeah.
[01:45:01] Even miracles need time.
[01:45:04] It's a good way to put it. I would I
[01:45:06] feel like that'd be very egotistical to
[01:45:07] call this a miracle. It's certainly not.
[01:45:09] It's just an experiment that we'll see
[01:45:11] what happens, but yeah, it's a good way
[01:45:13] to put it.
[01:45:16] All right.
[01:45:20] That's very cool John. I joined Dynamis
[01:45:22] two months ago today, never wrote a
[01:45:23] single line of code, have a functioning
[01:45:25] second brain.
[01:45:26] And yeah, that's that's awesome John. I
[01:45:28] appreciate it. Once you get to that
[01:45:29] point where your second brain is up and
[01:45:31] running and saving hours and hours every
[01:45:32] week there is no better feeling. So
[01:45:35] good.
[01:45:37] All right.
[01:45:43] One of the basic rules of marketing is
[01:45:45] people are willing to pay for high
[01:45:46] ticket. I mean that's fair. Yeah, like
[01:45:48] this individual that I mentioned
[01:45:51] I mean maybe I could just say his name
[01:45:52] cuz I'm really not like hating on him or
[01:45:54] anything, but I just for the sake of
[01:45:56] being careful.
[01:45:57] I'm sure there are people that get a lot
[01:45:59] of value out of it and and yeah, he he
[01:46:01] like kind of is known as like the
[01:46:03] premium person.
[01:46:05] He's like he's been building second
[01:46:07] brains for a decade.
[01:46:09] I mean I would like to think that like
[01:46:10] he's struggling to catch up with all the
[01:46:12] AI stuff cuz he he's more traditional in
[01:46:14] his approach. He's probably doing fine,
[01:46:15] but anyway like yeah, I'm sure there's
[01:46:18] When you when you have something high
[01:46:19] ticket, it signals value and so you do
[01:46:21] attract that kind of person that is
[01:46:24] willing to shell out
[01:46:26] and they just want to make sure like I
[01:46:28] mean I don't always agree with this, but
[01:46:29] like sometimes people just think like
[01:46:31] hey, most money means it's the best
[01:46:33] value.
[01:46:34] Definitely isn't always true, but it
[01:46:36] does kind of scream like this is going
[01:46:38] to be the safest bet if you have the
[01:46:39] money for it. I don't know. I don't
[01:46:41] know. Kind of rambling on that, but
[01:46:43] Yeah.
[01:46:45] Uh
[01:46:47] Dynamis is awesome. I'm part of the
[01:46:48] community since it came live. That's so
[01:46:50] cool. I appreciate you being a part of
[01:46:51] the community for so long.
[01:46:53] And by the way, the 1-year anniversary
[01:46:56] of Dynamis is this month, April 26th.
[01:47:01] So there going to be some some exciting
[01:47:03] things that I've got going on for that.
[01:47:04] Some live streams I'll be doing on
[01:47:06] YouTube around the time
[01:47:08] and also some exciting events in Dynamis
[01:47:10] and some things that I am releasing as a
[01:47:12] part of the anniversary celebration.
[01:47:14] Also just speaking of things that are
[01:47:16] going on around that time,
[01:47:18] I want to call this out really quick as
[01:47:19] well. I'm doing a This is kind of
[01:47:21] unrelated, but around the same time.
[01:47:24] I'm doing an AI transformation workshop
[01:47:26] with
[01:47:27] a gentleman named Lior Weinstein on
[01:47:30] April 28th. So that I believe that's a
[01:47:32] Tuesday at 9:00 a.m. [snorts] Central
[01:47:34] time.
[01:47:36] So this is going to be really cool
[01:47:37] because
[01:47:38] Lior he's like an expert at coming into
[01:47:41] a company and helping it become AI
[01:47:43] native.
[01:47:45] And so like designing like an AI native
[01:47:47] org chart and like how to enable each
[01:47:49] team and team member with AI
[01:47:51] technologies for coding and other things
[01:47:54] like even just like you know the sales
[01:47:56] and marketing and finance team and all
[01:47:57] of that.
[01:47:58] So he's going to like talk about that
[01:47:59] for an hour and then for an hour I'm
[01:48:02] going to talk about how to transform
[01:48:04] your organization with agentic coding
[01:48:06] and like how to transform developer
[01:48:07] teams. So we're going to kind of take
[01:48:09] team it together to give you like this
[01:48:10] full view of like how you transform
[01:48:13] companies and even yourself as an
[01:48:14] individual.
[01:48:16] So that's going to be really cool. So
[01:48:17] that's happening at the end of this
[01:48:18] month here.
[01:48:20] And yeah, like you can see I'm on my you
[01:48:22] know scheduled live stream page of my
[01:48:23] channel. Like this is just going to be a
[01:48:25] free workshop just [clears throat]
[01:48:27] happening on live stream on my channel.
[01:48:32] All right.
[01:48:35] Cool. Yeah, big shout out to Cole. Even
[01:48:37] the content you're delivering for free
[01:48:38] every week is insane. Thanks a lot.
[01:48:40] Yeah, you're very welcome. Always my
[01:48:42] pleasure. Man, like I've been doing
[01:48:43] YouTube for
[01:48:45] it's almost 2 years now. I started like
[01:48:48] very beginning of July 2024.
[01:48:51] And it's just a blast. Every single
[01:48:53] video is just so fun to make and
[01:48:56] keeps me ahead of the curve on
[01:48:57] everything too. Just being a constantly
[01:48:59] in the trenches building and researching
[01:49:01] and doing what it takes to make the
[01:49:02] content for you guys.
[01:49:06] All right.
[01:49:09] What is going on now?
[01:49:12] >> [laughter]
[01:49:12] >> Uh, sometimes it's stressful to come
[01:49:14] back and just see like it's in the
[01:49:15] middle of writing the package.json. You
[01:49:17] don't even know why.
[01:49:19] Oh, I guess it Oh, yeah, it's setting up
[01:49:20] the developer dependencies that we
[01:49:22] talked about. Okay, we're good. We're
[01:49:23] good.
[01:49:24] So, okay, what has it done now? I think
[01:49:27] it made the full workflow.
[01:49:30] Yeah, okay. Dark Factory fix GitHub
[01:49:32] issue. Okay, good. So, we got our second
[01:49:34] workflow now.
[01:49:36] All right.
[01:49:37] Dynamis Oh, no, not that one. I need to
[01:49:39] go to
[01:49:41] the rag YouTube chat. I want to open up
[01:49:43] the second workflow.
[01:49:45] Okay, take then this is good. So, now we
[01:49:46] have all our different commands. So,
[01:49:50] instead of the workflow just being like
[01:49:51] a bunch of massive inline prompts, uh we
[01:49:54] got it organized a lot better.
[01:49:57] Okay, so this is our fix GitHub issue.
[01:49:59] By the way, I'm thinking about renaming
[01:50:01] the whole
[01:50:02] uh rag YouTube chat repo to Dyna chat.
[01:50:05] That's why it references this name a
[01:50:07] couple times.
[01:50:09] Uh but anyway, so
[01:50:11] this workflow here, we're going to start
[01:50:12] by extracting the issue number. So, this
[01:50:15] is very much based based on the default
[01:50:17] fix GitHub issue workflow in Arkon. Then
[01:50:19] we classify the issue, bug, feature,
[01:50:22] enhancement, refactor, chore, or
[01:50:24] documentation, just like we planned in
[01:50:26] the in the Dark Factory plan. Then we
[01:50:28] research the issue.
[01:50:30] Uh and then we either do a plan, we
[01:50:32] create a plan if it is a feature to
[01:50:35] build, or we investigate the problem if
[01:50:38] it is a bug to fix, right? Cuz issues
[01:50:40] are going to be one of the two.
[01:50:42] Right? So, like when we classify, it's
[01:50:44] either going to be a bug, and then I
[01:50:46] know we have all these different labels,
[01:50:47] but basically all these are just feature
[01:50:48] additions, right? Like if it's a chore
[01:50:50] or a refactor or an enhancement, like
[01:50:53] all those are just like more specific
[01:50:54] versions of a feature. So, may maybe the
[01:50:57] whole like issue labeling isn't
[01:50:59] optimized here, but I think it's fine.
[01:51:01] It's actually pretty standard to have
[01:51:03] those kinds of labels.
[01:51:05] And then we go into implementation, then
[01:51:07] validation, create the pull request, and
[01:51:10] we review. And so, I am going to have a
[01:51:12] separate workflow to do complete pull
[01:51:15] request validation, but I still want to
[01:51:17] have the workflow it's like when the PR
[01:51:20] is created, at least have it do a little
[01:51:21] bit of review, right? So, like initial
[01:51:24] round of review here, and then it'll
[01:51:25] have a more comprehensive validate PR
[01:51:27] workflow that I'll create next. That's
[01:51:29] the plan.
[01:51:31] Just to give it a chance to do a little
[01:51:32] bit of self-fixing before we say like,
[01:51:34] "All right, here's our pull request for
[01:51:36] for you, uh you know, next stage of Dark
[01:51:38] Factory to review."
[01:51:45] All right.
[01:51:49] So, let's go back to our coding agent
[01:51:50] here.
[01:51:53] Where am I going? Okay, there we go.
[01:51:57] Okay, status so far. So, we refactored,
[01:52:00] built the new workflow, seven new
[01:52:02] commands.
[01:52:03] Looking good. Got our dependency set up.
[01:52:06] Uh okay, before I kick off the smoke
[01:52:09] test, two things to confirm. Dev
[01:52:11] dependencies are not installed locally.
[01:52:15] Um
[01:52:17] okay, that's fine.
[01:52:19] Yes, I want you to install the dev
[01:52:21] dependencies. And actually, I would much
[01:52:23] prefer to use UV for the Python package
[01:52:26] management, so go ahead and change that
[01:52:27] in the repository. Get everything
[01:52:29] installed and test everything.
[01:52:32] And
[01:52:33] um
[01:52:34] and then yes, go ahead and invoke after
[01:52:35] that invoke the Arkon workflow to run
[01:52:38] the Dark Factory fix GitHub issue on
[01:52:40] pull request or no, on issue number 26.
[01:52:47] Okay, yep, that's good. All right, cool.
[01:52:52] And then we're not going to have time
[01:52:53] for it in the live stream here, but um
[01:52:56] you know what I
[01:52:57] I'm almost tempted to do another live
[01:52:59] stream tomorrow instead of a YouTube
[01:53:00] video. Maybe. I probably should make a
[01:53:02] YouTube video cuz it it'll be a week.
[01:53:05] Uh but it'd be cool to like just keep
[01:53:06] building this live more. I know that
[01:53:08] it's a lot of time, but it it's it's fun
[01:53:11] to do this, and we're getting kind of
[01:53:13] close, right? Like we have a lot of it
[01:53:15] built. We just need to finish the last
[01:53:17] couple of workflows, and then we need to
[01:53:19] bring everything onto the VPS so that we
[01:53:21] have the whole Dark Factory running
[01:53:23] autonomously, and it's not relying on my
[01:53:25] computer being on. So, we're we're
[01:53:27] getting there. We're getting there.
[01:53:30] We we won't really be unfortunately be
[01:53:32] able to see everything running on our
[01:53:34] VPS today,
[01:53:36] but um
[01:53:38] it won't take long once we have the
[01:53:40] workflows built and validated to copy
[01:53:43] everything over cuz we already have the
[01:53:46] I think this is my directory, Dark
[01:53:49] Factory. Yeah, yeah. So, we already have
[01:53:51] the app here. So, we we already have
[01:53:53] everything like cloned and set up and
[01:53:55] verified. So, we just have to bring over
[01:53:56] the workflows and then set up the cron
[01:53:58] job that's going to run every hour to do
[01:54:00] the triaging and then the implementation
[01:54:02] and everything. Like it it should
[01:54:04] work pretty quick once we have the
[01:54:06] workflows built. And that's why I wanted
[01:54:07] to use Arkon for this because then I'm
[01:54:10] not even creating the harness myself
[01:54:12] from scratch. I'm just building Arkon
[01:54:14] workflows, and that is the harness. It's
[01:54:15] a clear example of the value of Arkon as
[01:54:19] a harness builder, which is part of the
[01:54:20] reason I wanted to do this Dark Factory,
[01:54:22] by the way, is it's just such a cool use
[01:54:24] case to show the power of Arkon. Like
[01:54:27] these workflows are defining processes
[01:54:29] that would actually take a good amount
[01:54:31] of time to architect from scratch. If we
[01:54:33] wanted to like, for example, even just
[01:54:36] having this process of triaging issues
[01:54:39] and then sending off
[01:54:41] MiniMax to handle each one of these in
[01:54:44] parallel, like that would take a lot of
[01:54:46] engineering if we didn't have Arkon as a
[01:54:47] starting point to bring in the context
[01:54:50] and handle work trees for isolation so
[01:54:52] we can build each one of them in
[01:54:53] parallel. And then having the
[01:54:55] deterministic steps to uh you know,
[01:54:57] label the issues and close issues, like
[01:55:00] that that's a lot of work, but now we're
[01:55:02] able to just rip through this like
[01:55:04] pretty quick. Like I know that it that
[01:55:06] the stream is like 2 hours now, but
[01:55:09] still like when you really think about
[01:55:11] how much we've already engineered here,
[01:55:13] like it's a lot that we've built
[01:55:15] already, and we've taken our time with
[01:55:17] it.
[01:55:19] All right.
[01:55:26] Um
[01:55:28] >> [laughter]
[01:55:28] >> Can we use Arkon and the Dark Factory as
[01:55:30] paperclip?
[01:55:32] So, yes. You could.
[01:55:36] Cuz each Arkon workflow could be like
[01:55:38] the
[01:55:39] the you know, individual AI employee,
[01:55:41] kind of like how you manage that with um
[01:55:44] paperclip. You could.
[01:55:46] That'd be cool. It's kind of what I'm
[01:55:48] doing, I guess. Like each Arkon workflow
[01:55:50] you could sort of think of as a
[01:55:50] different employee. I mean, we literally
[01:55:53] have the pattern here where we're doing
[01:55:55] the about the holdout where it's like
[01:55:56] this has to run completely separately
[01:55:58] from the implementation. So, it is sort
[01:56:00] of like two different AI employees that
[01:56:03] the the Dark Factory is delegating work
[01:56:06] to.
[01:56:10] Smooth as fast. Mistakes are 10x as
[01:56:13] expensive as planning time. That's
[01:56:14] right. Pays dividends take your time up
[01:56:16] front.
[01:56:23] All right.
[01:56:30] Let's see. Learned a bunch about rag
[01:56:32] from you early on. Yeah, I still cover
[01:56:34] rag somewhat, not as much anymore, but
[01:56:36] it is still important. A lot of that old
[01:56:39] content is still very relevant, too.
[01:56:41] But yeah, I used to I definitely used to
[01:56:43] be like the rag guy back in the day, but
[01:56:46] especially when I first started my
[01:56:47] channel.
[01:56:48] Yeah.
[01:56:51] The appearance of value is very
[01:56:52] important. 100% yeah. I had a relative
[01:56:55] doing art and selling at craft shows.
[01:56:56] She switched to art shows and made a
[01:56:58] living off of it and has pieces in
[01:57:00] museums. That is so cool. Yeah. Right,
[01:57:02] so it kind of goes back to our
[01:57:03] conversation earlier, like when you have
[01:57:05] something priced at high ticket, like if
[01:57:06] you have the good appearance of value,
[01:57:08] you can price it high, like 100%
[01:57:10] Yeah.
[01:57:14] All right.
[01:57:23] Providing unique individual value via
[01:57:26] video platforms, cohort platforms, etc.
[01:57:28] is the norm of the future, not the
[01:57:30] exception.
[01:57:32] Yeah, I mean, people will crave
[01:57:34] individual attention and personalization
[01:57:37] more and more over time as AI takes it
[01:57:39] away in some parts of life, so
[01:57:42] I can see what you're saying. Yep.
[01:57:46] Um
[01:57:49] Maybe Cole has an AI-proof job. How many
[01:57:51] people would watch this stream if his
[01:57:53] second brain was doing it alone?
[01:57:56] >> [laughter]
[01:57:57] >> Oh, that'll be the day. I don't I don't
[01:57:59] know if I would ever want to have my
[01:58:00] second brain run a live stream. Also, I
[01:58:02] would it wouldn't look good right now.
[01:58:05] But I mean, there are people that have
[01:58:07] AI avatars do videos, not necessarily
[01:58:09] live streams, but even that, like it
[01:58:10] just looks bad. I I don't I don't think
[01:58:13] that it's really feasible.
[01:58:16] >> [snorts]
[01:58:16] >> Um unless like
[01:58:18] for some reason people are okay with it
[01:58:20] being an AI avatar cuz you're just like
[01:58:22] delivering the news or something. I know
[01:58:23] that that's usually what most AI avatar
[01:58:25] channels, they are just like AI
[01:58:27] news-focused, right?
[01:58:35] All right.
[01:58:37] If you're paying 2K to learn how to use
[01:58:38] Zettelkasten, then you may need more
[01:58:40] than a second brain.
[01:58:42] Uh
[01:58:45] That's funny. Yeah, I don't I don't
[01:58:47] know, like you can get pretty deep with
[01:58:49] Zettelkasten. I know myself personally,
[01:58:51] I've only scratched the surface. I have
[01:58:52] actually taken inspiration from
[01:58:54] Zettelkasten a little bit for how I've
[01:58:56] organized my Obsidian vault.
[01:58:58] But yeah, it's definitely something I I
[01:59:00] personally like I agree, I feel like you
[01:59:02] can just figure it out on your own if
[01:59:05] you have a good head on your shoulders,
[01:59:06] but again, to each their own. I'm I'm
[01:59:09] trying to like avoid getting like super
[01:59:10] opinionated on things that like I know
[01:59:13] that like there is value
[01:59:15] but
[01:59:17] yeah, it just depends how much you want
[01:59:18] to just like get the best practices
[01:59:20] right away versus like figure out
[01:59:21] yourself over time. I guess is what it
[01:59:22] comes down to.
[01:59:26] All right.
[01:59:30] What else we got here?
[01:59:36] Yeah, okay. So this is exactly why I
[01:59:38] built my own get up issue fixed workflow
[01:59:41] for just now.
[01:59:42] The default Archon commands are very no
[01:59:44] JS centric and that I think that is
[01:59:46] something we want to improve to make it
[01:59:47] a bit more language agnostic or a lot
[01:59:49] more language agnostic.
[01:59:51] I can see arguing with itself to build
[01:59:53] my go laying app.
[01:59:55] Yeah, so I would recommend right now. I
[01:59:57] mean just in general it's good to build
[01:59:59] your own hardness. Build your own
[02:00:00] workflows cuz then you can customize it
[02:00:02] more.
[02:00:03] I would recommend building your own and
[02:00:05] using the ones that we have as defaults
[02:00:07] as a starting point. So you can point
[02:00:09] your coding agent to the default Archon
[02:00:12] workflows and say look at these for a
[02:00:14] best practices and even like leveraging
[02:00:16] the structure for fixing issues or
[02:00:18] creating PRDs or validating pull
[02:00:20] requests.
[02:00:21] And like use that as a starting point
[02:00:23] and then make it specific to my
[02:00:25] validation flow or my tech stack or my
[02:00:27] architecture.
[02:00:30] Yeah.
[02:00:32] Cool.
[02:00:33] The AI co-host.
[02:00:36] Okay, that could actually be
[02:00:37] interesting.
[02:00:38] If I had my second brain not like run
[02:00:40] the stream but just like be there as a
[02:00:43] peanut gallery or something more
[02:00:46] practical like kind of giving feedback
[02:00:48] in real time or even like answering some
[02:00:50] questions in the chat.
[02:00:52] I could Okay, that could actually be
[02:00:54] kind of cool. I should think about that.
[02:00:56] How I could have my second brain co-host
[02:00:58] a live stream with me.
[02:01:00] That would be cool.
[02:01:02] Hmm. Okay, I'll think about that. I will
[02:01:05] definitely think about that.
[02:01:07] Okay. All right, where are we at now?
[02:01:11] Um oh, it's still going. Jeepers.
[02:01:15] All right.
[02:01:16] Well, I guess Oh, yeah, cuz we had the
[02:01:17] memory compaction. So that slowed things
[02:01:19] down a lot.
[02:01:22] Okay.
[02:01:23] >> [snorts]
[02:01:24] >> I'm I just wanted to
[02:01:27] Okay, I'll let it keep running here.
[02:01:30] All right.
[02:01:31] Then you don't need me anymore. No, no,
[02:01:34] no. I still I still want real people to
[02:01:36] help co-host live streams with me. So
[02:01:39] Thomas, he's the guy that I have the
[02:01:42] comment highlighted for and then also
[02:01:44] Rasmus. They've done a lot of amazing
[02:01:46] work helping me on Archon.
[02:01:48] And I have said that like for some
[02:01:49] Archon live streams, I'd love to get
[02:01:50] them in to co-host.
[02:01:52] And I still stand by that. There's no
[02:01:54] way if I get my second brain to help
[02:01:56] co-host with me, it would be a different
[02:01:58] kind of thing and a different sort of of
[02:02:01] value proposition for the live stream
[02:02:04] compared to having a real person like
[02:02:06] you or Rasmus co-host with me. Like I
[02:02:09] would want to do both 100%.
[02:02:12] Yeah.
[02:02:13] >> [laughter]
[02:02:15] >> All right.
[02:02:19] All right.
[02:02:24] Let's see.
[02:02:26] All right.
[02:02:28] We got some interesting feedback here.
[02:02:30] All right, let's take a look. Once you
[02:02:31] take this to production, it will just
[02:02:33] hallucinate success at every step. LLMs
[02:02:35] give the most plausible answer. They
[02:02:37] rationalize anything they can't reason.
[02:02:39] This whole video is from 2025.
[02:02:42] All right, hot take hot take but no, I
[02:02:44] appreciate the pushback.
[02:02:46] Um because what you're saying has some
[02:02:48] validity and that's why I'm calling it
[02:02:50] an experiment. And that's also why I'm
[02:02:53] spending so much time up front planning
[02:02:55] the system and the architecture.
[02:02:57] Because yes, one of the biggest problems
[02:02:59] with large language models right now is
[02:03:02] that they are sycophantic. They always
[02:03:05] agree with everything that we say and
[02:03:07] they have an insane amount of bias
[02:03:08] towards their own opinions. They're
[02:03:10] going to rationalize everything and
[02:03:12] there is a risk if we don't build the
[02:03:14] system right that they're going to say
[02:03:15] that this thing is ready to merge and
[02:03:17] then it's going to merge it and then
[02:03:18] it's going to move on to the next issue
[02:03:19] and we go through this loop where every
[02:03:21] single time it's producing AI slop. That
[02:03:24] is a risk.
[02:03:25] But that's what I'm trying to engineer
[02:03:27] for here.
[02:03:28] I'm putting so much time up front
[02:03:29] because I'm doing things like defining
[02:03:31] the holdout pattern for validation. So
[02:03:34] that I'm taking away for some of this
[02:03:36] I'm taking away from and preventing some
[02:03:38] of the sycophantic behavior. Because
[02:03:40] when we go into our regression testing,
[02:03:42] we don't even know what was just built.
[02:03:44] And so it's just going to be a
[02:03:46] neutral judge. At least that's the goal
[02:03:49] of what we're doing here. There's still
[02:03:50] a risk to it 100% and that's why I'm
[02:03:53] very clear at the start of the stream
[02:03:55] here that when we go to this level of
[02:03:58] autonomy for our coding agents. Like
[02:04:00] going back to the five levels here, the
[02:04:01] dark factory here is not what I
[02:04:04] recommend if you want the most reliable
[02:04:06] software possible. We might get there at
[02:04:09] some point and maybe this experiment is
[02:04:11] going to be a wild success and it's
[02:04:13] going to be like whoa, dang. Actually
[02:04:14] this can get us a really good, you know,
[02:04:16] MVP for any application.
[02:04:19] Maybe. But yeah, I'm I'm not I'm not
[02:04:22] like numb to the fact that sycophantic
[02:04:25] or sycophancy is a big problem and we
[02:04:28] have to be really careful about that.
[02:04:30] So I I feel pretty confident in the
[02:04:32] approach that I have here. I think we
[02:04:35] are going to avoid a lot of that bias
[02:04:37] and a lot of shipping things that it
[02:04:38] says are good when they actually aren't.
[02:04:40] It's not going to be perfect but that's
[02:04:42] also why I have other strategies. Like I
[02:04:44] have the like really deep regression
[02:04:46] testing that I'm going to run every day
[02:04:47] or every week and then create more
[02:04:49] issues to address that. I still am going
[02:04:51] to have some human in the loop for the
[02:04:53] very very end. Um where I actually want
[02:04:56] to like push things to a platform that
[02:04:58] people are using. So I'll have a little
[02:05:00] bit like I've thought about a lot of it.
[02:05:02] So again, I appreciate the pushback.
[02:05:04] But trust me, I'm I'm considering it all
[02:05:07] 100%.
[02:05:09] Okay, let's go back.
[02:05:10] Still working. Wow, okay.
[02:05:18] All right.
[02:05:21] Anime girl co-host. You'll never see me
[02:05:23] do that.
[02:05:24] >> [laughter]
[02:05:25] >> It's funny though.
[02:05:27] All right.
[02:05:30] You have to check the parameters to
[02:05:32] themselves introduce the specific
[02:05:33] parameters to check. Yeah,
[02:05:36] extra math and type of engineering
[02:05:37] checks to achieve it.
[02:05:39] A little lost on what you're getting at
[02:05:41] there. Maybe you could elaborate.
[02:05:45] Uh need to drop off. Good session Cole.
[02:05:48] I appreciate it.
[02:05:50] Yeah.
[02:05:51] All right.
[02:05:53] Cole the rag guy, spicy mangoes. Yeah,
[02:05:56] spicy mangoes hasn't come up for a while
[02:05:58] but I'll have to bring it in to another
[02:06:00] video soon.
[02:06:02] Um
[02:06:04] An LLM can't even join
[02:06:07] a a chat room
[02:06:09] without everyone knowing instantly it's
[02:06:11] an AI. I mean yes, that's true.
[02:06:14] Yep. That's that's why I wouldn't ever
[02:06:16] have a stream of having a second brain
[02:06:18] run anything anytime soon.
[02:06:20] Yep.
[02:06:22] All right.
[02:06:28] Let's see.
[02:06:33] Hard to explain. Yeah, all good. Yeah,
[02:06:34] take your time.
[02:06:37] All right.
[02:06:40] Yeah, okay. I agree with this 100%. If
[02:06:43] an LLM hosted a show, it would be boring
[02:06:44] and bland and obviously an LLM. I mean
[02:06:46] yes, I agree.
[02:06:49] All right.
[02:06:52] Um cool. So okay, anyway, our coding
[02:06:54] agent is done here. So I want to come
[02:06:56] back and and give it some more
[02:06:57] attention.
[02:06:58] So all right, we're done with all of our
[02:07:00] dev dependencies. The smoke test
[02:07:02] problem. Dark factory validate currently
[02:07:05] runs whole code base checks. If I kick
[02:07:06] off the workflow on number 26, the agent
[02:07:08] will
[02:07:10] fix the one line score bug then validate
[02:07:11] will hit 130 pre-existing errors didn't
[02:07:13] create.
[02:07:15] Um okay.
[02:07:17] So wow. Okay, so I guess what what
[02:07:19] happened here is we're creating the
[02:07:21] development environment for the first
[02:07:22] time. So there are a ton of issues that
[02:07:24] aren't actually related to the fix that
[02:07:28] we'd be running the workflow on. So I I
[02:07:29] need to actually address these things.
[02:07:35] Um
[02:07:38] Yeah.
[02:07:40] Let's do number one. Let's address all
[02:07:41] the problems and then run the workflow.
[02:07:46] Yeah, I just I mean this will take a
[02:07:48] while.
[02:07:50] Um but I I do just want to do that cuz
[02:07:52] cuz what I might be able to do is
[02:07:54] actually create the next workflow in
[02:07:55] another Claude code session here.
[02:07:59] I think that makes the most sense.
[02:08:02] Let's go ahead and do that.
[02:08:08] Okay.
[02:08:10] So let me go back to my vault
[02:08:12] and copy the path again
[02:08:14] to our plan file.
[02:08:21] So I'll say read this plan file
[02:08:25] and also load the Archon skills. You can
[02:08:27] help me build more Archon workflows.
[02:08:30] I have just finished creating my dark
[02:08:32] factory adaptation of the fixed get up
[02:08:34] issue workflow. Now I want to work on
[02:08:36] the validate PR workflow and it's very
[02:08:39] important that this follows the holdout
[02:08:40] pattern very closely.
[02:08:42] I just had someone in the live stream
[02:08:44] say that they don't believe in this
[02:08:45] approach and I think the holdout pattern
[02:08:47] is one of the most important things to
[02:08:49] address their concern. So let's let's
[02:08:50] focus on that.
[02:08:52] I'm being a little silly but but yeah, I
[02:08:54] think it's it is very important that we
[02:08:56] make sure that we are taking lessons
[02:08:58] from the strong DM dark factory cuz it
[02:09:01] is it is very impressive.
[02:09:07] All right.
[02:09:11] Let's see. What else we got in the chat
[02:09:12] here while I wait for this to run. We'll
[02:09:13] kind of monitor these two sessions in
[02:09:15] parallel here.
[02:09:19] Um is there a way to use Quen 3.6 plus
[02:09:22] with Archon even if it's through open
[02:09:24] router?
[02:09:26] So uh one thing I learned the hard way
[02:09:28] recently with open router is you're not
[02:09:30] actually able to use Claude code with
[02:09:33] open router for any models outside of
[02:09:35] the Anthropic ones cuz it doesn't have
[02:09:36] an an Anthropic um compatible endpoint
[02:09:39] like MiniMax and GLM.
[02:09:42] So if you wanted to use Quen 3.6 plus I
[02:09:45] would wait until we have support for uh
[02:09:48] Pi. Pi is going to be the third provider
[02:09:50] that we add this week or next into
[02:09:53] Archon.
[02:09:54] Because then you'll be able to use other
[02:09:55] models really easily. You're not going
[02:09:57] to be like the obviously like right now
[02:09:59] we have Claude and Codex and you're a
[02:10:00] little bit more vendor locked. You can
[02:10:02] do what I did in the VPS to point it to
[02:10:05] other providers but only if they are
[02:10:07] Anthropic compatible like MiniMax and
[02:10:09] GLM.
[02:10:10] So there might be a way but I actually
[02:10:12] tried first before I went to MiniMax
[02:10:15] directly. I tried going through open
[02:10:16] router and it didn't work.
[02:10:18] It only worked when I chose an Anthropic
[02:10:20] model.
[02:10:27] Um okay.
[02:10:29] It's confused here because it's trying
[02:10:31] to read my workflows in the remote
[02:10:33] machine but I haven't actually pushed it
[02:10:35] to remote yet.
[02:10:43] I might need to. Hold on.
[02:10:46] Oh no, hold on. It figured it out. We're
[02:10:47] good. We're good. All right.
[02:10:57] I need a new open source 120B.
[02:11:00] I mean yeah, it's been a while since we
[02:11:01] had one around that size for sure.
[02:11:04] Yeah.
[02:11:07] All right.
[02:11:08] Um since I love C
[02:11:11] what do you think about Blitzys and
[02:11:12] their C compilers?
[02:11:16] Um I don't Do I love C? I haven't
[02:11:18] programmed in C for a very long time.
[02:11:20] Actually it's been about 5 years since I
[02:11:23] programmed in C.
[02:11:25] Uh you mean like C the programming
[02:11:26] language?
[02:11:28] I assume cuz you're talking about C
[02:11:29] compiler. I I haven't used C in a long
[02:11:31] time. I also haven't heard about Blitzy.
[02:11:34] I'd be interested though. Um
[02:11:36] funny story or not funny but interesting
[02:11:38] fact for you guys.
[02:11:40] Um when I was in college I was a
[02:11:42] teacher's assistant for a C and machine
[02:11:45] learning course.
[02:11:47] So I I got to uh not sorry, not machine
[02:11:50] learning. Goodness. A C and assembly
[02:11:52] course, machine architecture course. So
[02:11:54] I got to help students debug assembly
[02:11:56] code for hours and hours a day.
[02:11:58] >> [laughter]
[02:11:58] >> At one point that was fun.
[02:12:01] Yeah.
[02:12:05] All right.
[02:12:06] So all right, what did it What do we got
[02:12:08] now? Have enough context. Let me lay out
[02:12:10] what I'm building. So holdout pattern
[02:12:11] design for the dark factory validate PR.
[02:12:14] This is the critical workflow for
[02:12:16] defending the AI writes code on
[02:12:18] supervised concern. Here's how I'll
[02:12:20] enforce strict holdout across five
[02:12:22] layers. Okay, so this is the main
[02:12:23] concern that we're addressing here with
[02:12:24] AI sycophancy in our dark factory.
[02:12:28] Not saying this is going to be perfect
[02:12:30] but this is my first attempt for the
[02:12:32] public experiment to avoid the coding
[02:12:35] agent just always saying its work is
[02:12:36] good and merging it.
[02:12:38] So we have a separate Archon workflow,
[02:12:41] separate artifact directory, separate
[02:12:43] work tree. There is no way that it can
[02:12:45] peer into the work of the other agent
[02:12:46] and potentially take its bias.
[02:12:50] So we exclude comments and review. No
[02:12:53] code no coder chatter.
[02:12:55] Uh we have our our governance files.
[02:12:59] So we're going to read those as our rule
[02:13:01] book.
[02:13:02] Every AI node is going to start with
[02:13:04] fresh context. So every step of the way
[02:13:06] during the validation we're not even
[02:13:07] going to build up bias in the validation
[02:13:09] itself through the different nodes.
[02:13:12] The behavior behavioral validation
[02:13:14] command leads with a holdout rule
[02:13:16] section enumerating what it must not
[02:13:18] consider. It can't find and search for
[02:13:20] implementation plans, commit messages,
[02:13:22] coder rationale, prior review comments.
[02:13:25] It answers exactly one question. Does
[02:13:27] the diff solve the issue body?
[02:13:31] Very good.
[02:13:33] And then even another holdout pattern I
[02:13:35] I was kind of referencing earlier is
[02:13:37] like when we do the full regression
[02:13:39] testing every day or every week it also
[02:13:41] is going to have no knowledge of recent
[02:13:43] feature implementations or issues that
[02:13:45] we're in the middle of addressing,
[02:13:46] right? Like it just is going to answer
[02:13:47] the the straight question of like does
[02:13:49] this application work with all the user
[02:13:51] journeys we have laid out in the mission
[02:13:53] markdown?
[02:13:56] Good.
[02:13:58] All right. So now it's writing
[02:13:59] everything and we'll let it go. Both
[02:14:01] both of these are still running
[02:14:02] actually.
[02:14:04] So
[02:14:07] I'm going to open up the repo again.
[02:14:11] Cuz I can I I just want to show off the
[02:14:13] uh mission and factory rules just like
[02:14:15] really quick.
[02:14:18] So here's our mission document. So it
[02:14:20] it's uh decently concise, not too long
[02:14:23] but it covers um like the core of the
[02:14:26] application. What is DynaChat?
[02:14:30] Um who is it for?
[02:14:32] Uh patent still pending by the way. I
[02:14:34] might not keep the name either. We'll
[02:14:36] see. We'll see. Uh who is it for? The
[02:14:38] core capabilities of the applications.
[02:14:40] This is specifically calling out what is
[02:14:42] in scope. Like if I were to create an
[02:14:44] issue to add Google OAuth to the
[02:14:46] platform the triage is going to be like
[02:14:49] oh yeah, good. Let's mark this as
[02:14:50] accepted because it's literally in the
[02:14:52] scope for the mission.md.
[02:14:55] And then we also cover what is out of
[02:14:56] scope. What must the factory never
[02:14:58] build? Like we don't want it to add
[02:15:00] other YouTube channels. Like if someone
[02:15:02] created a GitHub issue we'd want that to
[02:15:03] be rejected because
[02:15:05] at least for now. I mean I could extend
[02:15:07] this application later but at least for
[02:15:08] now the scope of this app is for my
[02:15:11] YouTube content to be a resource for you
[02:15:13] guys.
[02:15:14] We don't want to you know allow someone
[02:15:16] to open an issue to swap the LLM. That
[02:15:19] would be bad for my credits.
[02:15:21] Uh we don't want to like add in payments
[02:15:24] or subscriptions. Like this is meant to
[02:15:25] stay free. We don't want to
[02:15:26] overcomplicate with a mobile app or a
[02:15:28] desktop desktop app. Like no like
[02:15:30] electron or Tauri app.
[02:15:33] Um so yeah, it's like things that we
[02:15:34] don't want to build.
[02:15:35] Uh hard invariants. Like things that we
[02:15:37] have to we absolutely have to keep the
[02:15:39] same so we can't allow for issues that
[02:15:41] would try to tweak the rate limiting or
[02:15:44] the authentication requirements, things
[02:15:46] like that.
[02:15:47] Uh ways we're allowing it to evolve and
[02:15:49] then quality standards.
[02:15:52] Right? Like that that's our mission.md.
[02:15:54] And then I can evolve this over time.
[02:15:55] This is sort of like my console. So like
[02:15:57] going back to the analogy here of like
[02:15:59] you have a car that doesn't even have a
[02:16:01] steering wheel. Well you're still going
[02:16:03] to have some kind of console to provide
[02:16:04] higher level directions. And so if I
[02:16:06] want to tweak the dark factory
[02:16:09] I still have the levers to pull because
[02:16:11] I can still change the factory rules or
[02:16:13] the mission.md or I can update the
[02:16:15] Archon workflows. So if I really want to
[02:16:17] and there's like a drastic issue that I
[02:16:19] just really need to fix I can make a
[02:16:21] commit myself just straight to the main
[02:16:23] branch. So I mean there's flexibility
[02:16:25] with this here.
[02:16:27] Uh but yeah, that's And then the factory
[02:16:29] rules. This file governs how the dark
[02:16:31] factory operates on this repo. So like
[02:16:34] here here's how we handle triaging,
[02:16:36] right? Like this is more context that we
[02:16:38] it's quite important to feed into the
[02:16:40] triage workflow.
[02:16:42] Here's how we implement things. Here are
[02:16:44] our requirements for pull requests. For
[02:16:45] example, I don't want to allow more than
[02:16:47] 500 lines cuz I want every single issue
[02:16:50] to be a small focused scope of work.
[02:16:52] That's one of the most important things
[02:16:53] for getting reliability out of our
[02:16:55] coding agents here.
[02:16:57] Quality gates for auto merge. Uh
[02:17:00] uh talking about the regression testing.
[02:17:01] I want to use the agent browser
[02:17:03] specifically.
[02:17:06] This is the Vercel agent browser CLI.
[02:17:09] It's an open source browser automation
[02:17:11] tool that I use a lot to test my front
[02:17:13] ends especially when I'm working on
[02:17:15] Archon itself. I'm using the agent
[02:17:16] browser skill. So I want this to be
[02:17:18] built into my larger regression testing
[02:17:20] workflow. It's going to
[02:17:22] Uh protected files that it's not allowed
[02:17:24] to change, right? I don't want it to
[02:17:25] change its own governance documents cuz
[02:17:27] this is my console, my lever to pull,
[02:17:29] not its own.
[02:17:31] Um how like rules around like when we
[02:17:34] should auto reject certain things.
[02:17:37] How we should escalate, cost and
[02:17:39] throughput. I mean I don't need to get
[02:17:41] like super deep into everything here but
[02:17:43] uh yeah, you can see like the factory
[02:17:45] rules gets more specific. Like this is
[02:17:46] quite a few lines of code here.
[02:17:49] How many is it in total?
[02:17:51] Uh sorry, not code, lines of markdown. I
[02:17:53] got Even this isn't like super long but
[02:17:55] it's 320 lines cuz there's quite a bit
[02:17:57] of specificity I want to supply there to
[02:17:59] really have my guardrails defined.
[02:18:03] All right.
[02:18:10] Have I you tried using prompts
[02:18:12] that presume failure and laziness? It
[02:18:14] can rationalize that too.
[02:18:17] Um I mean I've I've played around with
[02:18:18] that kind of thing in the past.
[02:18:21] Um
[02:18:22] it can rationalize that too. Are you
[02:18:23] saying that like that actually doesn't
[02:18:24] work or are you saying that uh that
[02:18:26] helps it rationalize or like helps it
[02:18:29] address problems?
[02:18:36] Let's see.
[02:18:37] You may want to leverage all your work
[02:18:39] with rag and build graph rag as the
[02:18:41] second brain. Obsidian as a second brain
[02:18:42] doesn't come close to graph rag but
[02:18:44] Obsidian is less set up.
[02:18:46] Yeah, I mean I've found Obsidian enough
[02:18:48] for me and like it's nice cuz it is less
[02:18:50] set up like you said but I mean, maybe
[02:18:52] at some point I will build a whole Greg
[02:18:54] graph rank system for my brain and share
[02:18:56] it.
[02:18:58] Could be cool.
[02:19:00] I still kind of wrestle with that might
[02:19:02] be over engineering.
[02:19:03] Depending on, you know, how much context
[02:19:05] you're storing in your brain.
[02:19:07] But I have that in the back of my mind
[02:19:10] for sure.
[02:19:13] Oh, it does work. Okay, cool. Yeah,
[02:19:15] yeah. I mean, that's a good idea then.
[02:19:17] So, like my validation process, I could
[02:19:19] have a workflow in the dark factory that
[02:19:21] says like, "Okay, I need you to assume
[02:19:23] or like not even not even tell it to
[02:19:25] assume." I just say like, "This agent
[02:19:27] was lazy. Go and figure out why it's
[02:19:29] lazy, what could be better about the
[02:19:30] implementation, and then like open up
[02:19:32] another issue or resolve it directly."
[02:19:35] All right, that I like the idea of
[02:19:36] building that in for sure.
[02:19:42] All right.
[02:19:45] Could I use Karpathy's auto research to
[02:19:48] improve the dark factory in the future?
[02:19:52] Uh tell plot twist it does not stop
[02:19:54] running and starts replication.
[02:19:56] Right. Some Yeah, maybe it will, who
[02:19:58] knows. Um so, yeah, I could use
[02:20:00] Karpathy's auto research.
[02:20:02] Basically, if I were to apply Karpathy's
[02:20:04] auto research, it would be a separate
[02:20:07] process that has control over actually
[02:20:09] editing these three files.
[02:20:11] Right? Cuz like the idea behind auto
[02:20:13] research is you have a a file that kind
[02:20:16] of dictates a larger system, like a
[02:20:18] model or a repo. And then that file you
[02:20:21] have a coding agent iterate on
[02:20:22] autonomously based on lessons that are
[02:20:24] learned from a feedback loop. So, I
[02:20:26] could build Karpathy auto research to
[02:20:29] like evolve these over time.
[02:20:31] So, like right now within the factory
[02:20:33] rules I have that that hard rule where
[02:20:36] it's not allowed to
[02:20:38] It's not allowed to change the govern
[02:20:41] governance, the constitution. But this
[02:20:43] is only for the agents that are dealing
[02:20:45] with the issues in pull requests. So, I
[02:20:46] could have a separate process that like
[02:20:48] its actual sole job is to evolve the
[02:20:50] governance over time.
[02:20:52] It's an interesting idea. I don't know
[02:20:54] if I want to take the autonomy that far
[02:20:55] right now cuz I really want this to be
[02:20:57] the lever that like only I am pulling on
[02:20:59] currently, but that could be a a natural
[02:21:01] evolution at some point. It'd be
[02:21:02] interesting for sure.
[02:21:06] Cool. Yeah, I appreciate all the ideas
[02:21:08] you guys are sharing here seriously.
[02:21:09] Like there there's so much to chew on.
[02:21:11] That's why I love this experiment
[02:21:12] because
[02:21:13] like the world becomes your oyster for
[02:21:15] the ways that you can evolve this and
[02:21:17] the things you can build with it as
[02:21:18] well. You can really apply this to any
[02:21:20] workflow and it's just cool being able
[02:21:22] to like use Archon to guide the entire
[02:21:24] thing as well.
[02:21:26] Um like every single line of code that's
[02:21:27] written here is written from an Archon
[02:21:29] workflow.
[02:21:31] So, yeah. All right. Uh let's go back
[02:21:34] and see where we're at now.
[02:21:36] Um okay.
[02:21:40] So, we built our third workflow here.
[02:21:43] And uh what's this one? This one is
[02:21:47] Okay, so this one is in the middle of
[02:21:48] actually testing the
[02:21:50] uh the second workflow that we built.
[02:21:52] Cool.
[02:21:54] So, probably have to wait a while for
[02:21:56] that to happen. I think I'm going to go
[02:21:57] ahead and call the stream here though
[02:21:58] because we'll have to wait a while until
[02:22:01] we have like the next big thing
[02:22:02] happening. So, I'll keep working on this
[02:22:04] after the stream and then I'll be making
[02:22:06] a YouTube video on this as well for
[02:22:08] tomorrow, which I'm excited about.
[02:22:11] So, yeah. All right.
[02:22:13] Uh let's go back to full frame here.
[02:22:15] I appreciate all of you guys being here
[02:22:17] today. This is a very different live
[02:22:19] stream to to build and like actually
[02:22:21] take my time with something. I've not
[02:22:22] really done that on a live stream
[02:22:24] before, so yeah, I appreciate all you
[02:22:26] guys' ideas and and questions as well.
[02:22:29] And um yeah, for anyone who didn't get a
[02:22:30] chance to get their question answered,
[02:22:32] like always feel free to comment on a
[02:22:34] video, join the Dynamis community as
[02:22:36] well cuz I'm active there every single
[02:22:38] day.
[02:22:39] Uh maybe I'll just show that uh one more
[02:22:40] time
[02:22:42] really quick here.
[02:22:44] I'll put a link once more in the chat
[02:22:45] here cuz yeah, if you want to build your
[02:22:47] own second brain, go through the agenda
[02:22:49] coding course, just ask any question
[02:22:52] that uh you have. Like the Dynamis
[02:22:54] community is the place for it. So, I'd
[02:22:56] love to see you there. Um otherwise,
[02:22:57] I'll I'll go back to my full frame here.
[02:23:01] But yeah, more live streams coming as
[02:23:02] well.
[02:23:03] Uh because I I actually enjoy doing live
[02:23:06] streams more than making YouTube videos.
[02:23:09] I like both, of course. I love both. But
[02:23:11] I love doing live stream. I love being
[02:23:12] live with you guys.
[02:23:14] So, yeah.
[02:23:16] All right. So, yeah, with that,
[02:23:17] appreciate all you guys being here. Uh
[02:23:20] stay tuned for the YouTube video
[02:23:21] tomorrow on the dark factory with Archon
[02:23:24] and more live streams coming up soon.
[02:23:27] Hope that you guys have a great rest of
[02:23:29] your day and I'll see you all around.
[02:23:32] Have a good one, guys.

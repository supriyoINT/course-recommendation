CREATE TABLE public.users (
	id int4 GENERATED ALWAYS AS IDENTITY NOT NULL,
	name varchar NULL,
	email varchar(100) NOT NULL,
	CONSTRAINT users_pk PRIMARY KEY (id),
	CONSTRAINT users_unique UNIQUE (email)
);


CREATE TABLE public.user_profile (
	id int4 GENERATED ALWAYS AS IDENTITY NOT NULL,
	user_id int4 NOT NULL,
	user_type varchar NULL,
	goal varchar NULL,
	interest_area _varchar NULL,
	experience_level varchar NULL,
	background varchar NULL,
	current_skills _varchar NULL,
	learning_purpose varchar NULL,
	preferred_learning_style varchar NULL,
	preferred_platforms _varchar NULL,
	budget varchar NULL,
	time_available_per_week varchar NULL,
	timeline varchar NULL,
	CONSTRAINT user_profile_pk PRIMARY KEY (id),
	CONSTRAINT user_profile_unique UNIQUE (user_id)
);

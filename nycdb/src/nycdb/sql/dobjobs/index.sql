-- bbl
create index dobjobs_bbl_idx on dobjobs (bbl);
-- bin
create index dobjobs_bin_idx on dobjobs (bin);
-- Latest Action Date
create index dobjobs_latestactiondate_idx on dobjobs (LatestActionDate DESC NULLS LAST);
create index dobjobs_latestactiondate_desc_idx on dobjobs (LatestActionDate DESC);
-- jobtype
create index dobjobs_jobtype_idx on dobjobs (JobType);
-- job status
create index dobjobs_jobstatus_idx on dobjobs (JobStatus);
-- community board
create index dobjobs_communityboard_idx on dobjobs (CommunityBoard);
-- existing/proposed # of stories
create index dobjobs_existingnoofstories_idx on dobjobs (ExistingNoofStories);
create index dobjobs_proposednoofstories_idx on dobjobs (ProposedNoofStories);

create index dob_now_jobs_bbl on dob_now_jobs (bbl);
create index dob_now_jobs_bin on dob_now_jobs (bin);
create index dob_now_jobs_jobfilingnumber on dob_now_jobs (JobFilingNumber);
create index dob_now_jobs_jobtype on dob_now_jobs (JobType);
create index dob_now_jobs_filingdate on dob_now_jobs (FilingDate DESC NULLS LAST);
create index dob_now_jobs_firstpermitdate on dob_now_jobs (FirstPermitDate DESC NULLS LAST);

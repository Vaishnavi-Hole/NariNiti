from django.db import models
from django.contrib.auth.models import User


SECTOR_CHOICES = [
    ('food_processing', 'Food Processing'),
    ('textiles_apparel', 'Textiles / Apparel'),
    ('beauty_wellness', 'Beauty & Wellness'),
    ('agriculture', 'Agriculture'),
    ('dairy', 'Dairy'),
    ('handicrafts', 'Handicrafts'),
    ('retail', 'Retail'),
    ('education', 'Education & Coaching'),
    ('technology', 'Technology & IT'),
    ('manufacturing', 'Manufacturing'),
    ('services', 'Services'),
    ('healthcare', 'Healthcare'),
    ('other', 'Other'),
]

BUSINESS_STAGE_CHOICES = [
    ('idea', 'Idea / Pre-launch'),
    ('startup', 'Startup (< 1 year)'),
    ('growth', 'Growth (1–3 years)'),
    ('established', 'Established (3+ years)'),
]

GENDER_CHOICES = [
    ('all', 'All'),
    ('female', 'Women Only'),
    ('male', 'Men Only'),
]


class GovernmentScheme(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    ministry = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=50, blank=True, help_text='Blank = national scheme')
    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES, blank=True)
    sector_keywords = models.JSONField(default=list, help_text='List of sector keywords for matching')
    business_types = models.JSONField(default=list)
    target_groups = models.JSONField(default=list)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='all')
    min_capital = models.BigIntegerField(null=True, blank=True)
    max_capital = models.BigIntegerField(null=True, blank=True)
    eligibility_text = models.TextField(blank=True)
    benefits_text = models.TextField(blank=True)
    documents_required = models.JSONField(default=list)
    official_website = models.URLField(blank=True)
    business_stages = models.JSONField(default=list, help_text='Applicable stages: idea, startup, growth, established')
    active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=True, help_text='Demo seed data, replace with verified production data')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Mentor(models.Model):
    name = models.CharField(max_length=150)
    expertise = models.JSONField(default=list, help_text='List of expertise areas')
    sectors = models.JSONField(default=list, help_text='Sectors they mentor in')
    languages = models.JSONField(default=list, help_text='Languages spoken')
    state = models.CharField(max_length=50, blank=True)
    district = models.CharField(max_length=100, blank=True)
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    availability = models.CharField(max_length=100, blank=True, default='Weekends')
    contact_method = models.CharField(max_length=200, blank=True)
    business_stages = models.JSONField(default=list)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class NGO(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    state = models.CharField(max_length=50, blank=True)
    district = models.CharField(max_length=100, blank=True)
    focus_areas = models.JSONField(default=list)
    services = models.JSONField(default=list)
    languages = models.JSONField(default=list)
    women_support = models.BooleanField(default=True)
    entrepreneurship_support = models.BooleanField(default=True)
    contact = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    verified = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class BusinessIdea(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_ideas')
    original_text = models.TextField()
    detected_language = models.CharField(max_length=20, blank=True, default='English')
    is_voice_input = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} — {self.title or self.original_text[:50]}'

    class Meta:
        ordering = ['-created_at']


class AIAnalysis(models.Model):
    idea = models.OneToOneField(BusinessIdea, on_delete=models.CASCADE, related_name='analysis')
    business_type = models.CharField(max_length=255, blank=True)
    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES, blank=True)
    location = models.CharField(max_length=255, blank=True)
    capital = models.BigIntegerField(null=True, blank=True)
    target_customers = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    experience = models.CharField(max_length=255, blank=True)
    business_stage = models.CharField(max_length=30, choices=BUSINESS_STAGE_CHOICES, default='idea')
    goal = models.TextField(blank=True)
    keywords = models.JSONField(default=list)
    required_support = models.JSONField(default=list)
    raw_gemini_response = models.JSONField(default=dict)
    is_vague = models.BooleanField(default=False)
    follow_up_questions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Analysis for idea {self.idea_id}'


class SchemeMatch(models.Model):
    idea = models.ForeignKey(BusinessIdea, on_delete=models.CASCADE, related_name='scheme_matches')
    scheme = models.ForeignKey(GovernmentScheme, on_delete=models.CASCADE)
    match_score = models.FloatField(default=0.0)
    semantic_score = models.FloatField(default=0.0)
    rule_score = models.FloatField(default=0.0)
    match_reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score']
        unique_together = ['idea', 'scheme']


class MentorMatch(models.Model):
    idea = models.ForeignKey(BusinessIdea, on_delete=models.CASCADE, related_name='mentor_matches')
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE)
    match_score = models.FloatField(default=0.0)
    match_reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score']
        unique_together = ['idea', 'mentor']


class NGOMatch(models.Model):
    idea = models.ForeignKey(BusinessIdea, on_delete=models.CASCADE, related_name='ngo_matches')
    ngo = models.ForeignKey(NGO, on_delete=models.CASCADE)
    match_score = models.FloatField(default=0.0)
    match_reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score']
        unique_together = ['idea', 'ngo']

from rest_framework import serializers
from .models import Quiz, Question, Option

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ['id', 'text', 'is_correct']

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'options']

    def create(self, validated_data):
        options_data = validated_data.pop('options')
        question = Question.objects.create(**validated_data)
        for option in options_data:
            Option.objects.create(question=question, **option)
        return question

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.save()

        # Update or create options
        options_data = validated_data.get('options', [])
        option_instances = instance.options.all()
        option_map = {option.id: option for option in option_instances}

        for option_data in options_data:
            option_id = option_data.get('id')
            if option_id and option_id in option_map:
                # Update existing option
                option = option_map[option_id]
                option.text = option_data.get('text', option.text)
                option.is_correct = option_data.get('is_correct', option.is_correct)
                option.save()
            else:
                # Create new option
                Option.objects.create(question=instance, **option_data)

        # Delete options that are no longer in the data
        for option_id in option_map:
            if not any(option_data.get('id') == option_id for option_data in options_data):
                option_map[option_id].delete()

        return instance

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'duration_minutes', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        quiz = Quiz.objects.create(**validated_data)
        for question_data in questions_data:
            options_data = question_data.pop('options')
            question = Question.objects.create(quiz=quiz, **question_data)
            for option_data in options_data:
                Option.objects.create(question=question, **option_data)
        return quiz

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        # instance.percentage_for_qualified = validated_data.get('percentage_for_qualified', instance.percentage_for_qualified)
        instance.duration_minutes = validated_data.get('duration_minutes', instance.duration_minutes)
        instance.save()

        # Update or create questions
        questions_data = validated_data.get('questions', [])
        question_instances = instance.questions.all()
        question_map = {question.id: question for question in question_instances}

        for question_data in questions_data:
            question_id = question_data.get('id')
            if question_id and question_id in question_map:
                # Update existing question
                question_serializer = QuestionSerializer(question_map[question_id], data=question_data, partial=True)
                if question_serializer.is_valid():
                    question_serializer.save()
            else:
                # Create new question
                question_serializer = QuestionSerializer(data=question_data)
                if question_serializer.is_valid():
                    question_serializer.save(quiz=instance)

        # Delete questions that are no longer in the data
        for question_id in question_map:
            if not any(question_data.get('id') == question_id for question_data in questions_data):
                question_map[question_id].delete()

        return instance
    
class QuizTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title']

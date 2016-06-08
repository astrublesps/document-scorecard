"""empty message

Revision ID: ed887f218146
Revises: 42497348e808
Create Date: 2016-05-24 08:24:24.095806

"""

# revision identifiers, used by Alembic.
revision = 'ed887f218146'
down_revision = '42497348e808'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ESP', schema=None) as batch_op:
        batch_op.add_column(sa.Column('not_equal', sa.Boolean(), nullable=True))

    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ESP', schema=None) as batch_op:
        batch_op.drop_column('not_equal')

    ### end Alembic commands ###
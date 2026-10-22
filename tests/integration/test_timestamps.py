from tests import factories as f


async def test_update_advances_updated_at_and_it_is_readable_after_commit(session):
    st = await f.student(session)
    await session.commit()
    created, before = st.created_at, st.updated_at

    st.first_name = "Петро"
    await session.commit()

    # Plain attribute access: an expired column would raise MissingGreenlet here.
    assert st.updated_at > before
    assert st.created_at == created
